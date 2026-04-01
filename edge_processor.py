# edge_processor.py
import json
import subprocess

def run_agent(script_name):
    """
    Runs an agent Python script and returns its JSON output.
    """
    result = subprocess.run(["python", script_name], capture_output=True, text=True)
    return json.loads(result.stdout)

if __name__ == "__main__":
    # Run both agents
    market_data = run_agent("agent_market.py")
    news_data = run_agent("agent_news.py")

    # Combine into a single payload
    combined_payload = {
        "timestamp": market_data["timestamp"],
        "market_data": market_data["data"],
        "news_data": {
            "macro": news_data["macro_news"],
            "tickers": news_data["ticker_news"]
        }
    }

    # Example: print or send to a message queue / API
    print(json.dumps(combined_payload, indent=2))