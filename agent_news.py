# agent_news.py
import requests
import json
from datetime import datetime

def get_macro_news():
    """
    Placeholder: fetch macroeconomic news headlines.
    """
    # Example: Replace with real API (NewsAPI, Bloomberg, etc.)
    return [
        {"headline": "Fed raises interest rates", "impact": "high"},
        {"headline": "Unemployment rate falls", "impact": "medium"}
    ]

def get_ticker_news(tickers):
    """
    Placeholder: fetch news by ticker symbol.
    """
    news_data = {}
    for ticker in tickers:
        news_data[ticker] = [
            {"headline": f"{ticker} earnings beat expectations", "impact": "high"}
        ]
    return news_data

if __name__ == "__main__":
    tickers = ["AAPL", "MSFT", "TSLA"]
    output = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "news_scanner",
        "macro_news": get_macro_news(),
        "ticker_news": get_ticker_news(tickers)
    }
    print(json.dumps(output, indent=2))