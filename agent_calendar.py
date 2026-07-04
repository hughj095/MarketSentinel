import json
import os
import re
import importlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape

import requests

try:
    openai = importlib.import_module("openai")  # pip install openai
except Exception:
    openai = None


MARKETWATCH_CALENDAR_URL = "https://www.marketwatch.com/economy-politics/calendar"
FF_CALENDAR_XML_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"


def _http_get_text(url, timeout=20):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _looks_like_bot_block(text):
    lowered = text.lower()
    signatures = [
        "please enable js",
        "disable any ad blocker",
        "captcha-delivery.com",
        "just a moment",
        "enable javascript and cookies",
    ]
    return any(sig in lowered for sig in signatures)


def _normalize_event(raw):
    return {
        "title": raw.get("title") or raw.get("eventName") or raw.get("name") or "Unknown",
        "country": raw.get("country") or raw.get("currency") or "Unknown",
        "datetime": raw.get("datetime")
        or raw.get("dateTime")
        or raw.get("releaseDate")
        or raw.get("date")
        or "Unknown",
        "impact": raw.get("impact") or raw.get("importance") or raw.get("volatility") or "Unknown",
        "actual": raw.get("actual") or "",
        "forecast": raw.get("forecast") or raw.get("consensus") or "",
        "previous": raw.get("previous") or "",
        "source_url": raw.get("url") or MARKETWATCH_CALENDAR_URL,
    }


def _extract_marketwatch_events_from_text(text):
    # The page format can vary; this extracts small JSON object fragments containing event fields.
    normalized = unescape(text)
    pattern = re.compile(r"\{[^{}]{0,2200}(?:eventName|consensus|actual|previous)[^{}]{0,2200}\}")
    candidates = pattern.findall(normalized)

    events = []
    for blob in candidates:
        snippet = blob
        snippet = re.sub(r"\bundefined\b", "null", snippet)
        try:
            obj = json.loads(snippet)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        if not any(k in obj for k in ("eventName", "title", "name")):
            continue
        events.append(_normalize_event(obj))

    unique = []
    seen = set()
    for event in events:
        key = (event["title"], event["country"], event["datetime"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(event)
    return unique


def scrape_marketwatch_calendar():
    html = _http_get_text(MARKETWATCH_CALENDAR_URL)
    if _looks_like_bot_block(html):
        raise RuntimeError("MarketWatch blocked automated scraping from this environment.")

    events = _extract_marketwatch_events_from_text(html)
    if not events:
        raise RuntimeError("MarketWatch page was reachable but no event objects were parsed.")
    return events


def scrape_forex_factory_xml():
    xml_text = _http_get_text(FF_CALENDAR_XML_URL)
    root = ET.fromstring(xml_text)

    events = []
    for evt in root.findall("event"):
        date = (evt.findtext("date") or "").strip()
        time = (evt.findtext("time") or "").strip()
        dt_value = f"{date} {time}".strip()
        events.append(
            {
                "title": (evt.findtext("title") or "Unknown").strip(),
                "country": (evt.findtext("country") or "Unknown").strip(),
                "datetime": dt_value or "Unknown",
                "impact": (evt.findtext("impact") or "Unknown").strip(),
                "actual": "",
                "forecast": (evt.findtext("forecast") or "").strip(),
                "previous": (evt.findtext("previous") or "").strip(),
                "source_url": (evt.findtext("url") or FF_CALENDAR_XML_URL).strip(),
            }
        )
    return events


def get_macro_calendar_events():
    errors = []

    try:
        return {
            "source": "MarketWatch",
            "events": scrape_marketwatch_calendar(),
            "fallback_used": False,
            "errors": [],
        }
    except Exception as exc:
        errors.append(f"MarketWatch scrape failed: {exc}")

    ff_events = scrape_forex_factory_xml()
    return {
        "source": "ForexFactory XML fallback",
        "events": ff_events,
        "fallback_used": True,
        "errors": errors,
    }


def _heuristic_decision(events):
    high = [e for e in events if str(e.get("impact", "")).lower() in ("high", "holiday")]
    medium = [e for e in events if str(e.get("impact", "")).lower() == "medium"]

    if len(high) >= 4:
        regime = "high_volatility_risk"
        action = "reduce position size; avoid new leveraged entries around release windows"
    elif len(high) >= 1 or len(medium) >= 4:
        regime = "elevated_event_risk"
        action = "tighten risk limits and monitor spread/slippage during releases"
    else:
        regime = "normal_event_risk"
        action = "standard risk posture with event-time alerts enabled"

    return {
        "risk_regime": regime,
        "recommended_action": action,
        "high_impact_count": len(high),
        "medium_impact_count": len(medium),
    }


def generate_llm_calendar_decision(calendar_payload):
    events = calendar_payload.get("events", [])
    if not events:
        return {
            "summary": "No economic calendar events were parsed.",
            "event_risk_assessment": "unknown",
            "key_events": [],
            "decision": {
                "risk_regime": "unknown",
                "recommended_action": "no action",
                "high_impact_count": 0,
                "medium_impact_count": 0,
            },
            "llm_used": False,
            "reason": "No events available",
        }

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or openai is None:
        return {
            "summary": "LLM unavailable; using deterministic rules over scraped calendar data.",
            "event_risk_assessment": "rule-based",
            "key_events": events[:8],
            "decision": _heuristic_decision(events),
            "llm_used": False,
            "reason": "OPENAI_API_KEY not set or openai package unavailable",
        }

    try:
        openai.api_key = api_key
        prompt = f"""
You are a macro risk assistant.
Analyze this economic calendar payload and return STRICT JSON with keys:
- summary
- event_risk_assessment
- key_events (array of up to 8 events)
- decision (object with: risk_regime, recommended_action, high_impact_count, medium_impact_count)

Economic calendar payload:
{json.dumps(calendar_payload, indent=2)}
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        parsed["llm_used"] = True
        return parsed
    except Exception as exc:
        return {
            "summary": "LLM call failed; falling back to deterministic risk logic.",
            "event_risk_assessment": "rule-based-fallback",
            "key_events": events[:8],
            "decision": _heuristic_decision(events),
            "llm_used": False,
            "reason": str(exc),
        }


if __name__ == "__main__":
    calendar_payload = get_macro_calendar_events()
    llm_result = generate_llm_calendar_decision(calendar_payload)

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "economic_calendar_monitor",
        "calendar_source": calendar_payload.get("source"),
        "fallback_used": calendar_payload.get("fallback_used", False),
        "errors": calendar_payload.get("errors", []),
        "calendar_events": calendar_payload.get("events", []),
        "decision_payload": llm_result,
    }
    print(json.dumps(output, indent=2))