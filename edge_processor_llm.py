# edge_processor_llm.py
import json
import subprocess
import openai  # pip install openai

openai.api_key = "YOUR_OPENAI_API_KEY"

def run_agent(script_name):
    result = subprocess.run(["python", script_name], capture_output=True, text=True)
    return json.loads(result.stdout)

def generate_llm_insights(market_json, news_json):
    """
    Sends market + news JSON to the LLM and gets a structured trading insight.
    """
    prompt = f"""
You are a financial AI assistant. Analyze the following market and news data and provide:
1. Market trend summary (bullish, bearish, neutral).
2. Highlight tickers with notable movement.
3. Highlight important macro news.
4. Suggested action per ticker (watch, buy, sell).

Market data:
{json.dumps(market_json, indent=2)}

News data:
{json.dumps(news_json, indent=2)}

Return JSON like:
{{
  "summary": "...",
  "ticker_actions": {{"AAPL": "buy", "MSFT": "watch", ...}},
  "macro_highlights": ["...", "..."]
}}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return json.loads(response.choices[0].message.content)

if __name__ == "__main__":
    market_data = run_agent("agent_market.py")["data"]
    news_data = run_agent("agent_news.py")
    
    llm_output = generate_llm_insights(market_data, news_data)
    
    print(json.dumps(llm_output, indent=2))