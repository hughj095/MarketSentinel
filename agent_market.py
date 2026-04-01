# agent_market.py
import yfinance as yf
import json
from datetime import datetime

def get_market_movement(tickers):
    """
    Scans market tickers for up/down movement and relative volume.
    """
    results = {}
    for ticker in tickers:
        data = yf.Ticker(ticker).history(period="1d", interval="5m")
        if data.empty:
            continue
        last = data['Close'].iloc[-1]
        prev = data['Close'].iloc[-2]
        change_pct = ((last - prev) / prev) * 100
        volume_ratio = data['Volume'].iloc[-1] / data['Volume'].mean()
        
        results[ticker] = {
            "last_price": float(last),
            "change_pct": round(change_pct, 2),
            "volume_ratio": round(volume_ratio, 2)
        }
    return results

if __name__ == "__main__":
    tickers = ["^DJI", "^GSPC", "^IXIC"]  # Dow, S&P500, Nasdaq
    output = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "market_scanner",
        "data": get_market_movement(tickers)
    }
    print(json.dumps(output, indent=2))