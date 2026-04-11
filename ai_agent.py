"""
ai_agent.py — Trading signal generator using OpenAI GPT-4o.
"""

import json
from openai import OpenAI
from datetime import datetime


def analyze_market(api_key, pair, ticker, indicators, recent_candles):
    """
    Returns a trading signal dict:
    { signal, confidence, reasoning, entry_price,
      stop_loss, take_profit, risk_score, key_factors }
    """

    client = OpenAI(api_key=api_key)

    prompt = f"""You are an expert crypto trading analyst. Analyze this data for {pair} and return a trading signal.

MARKET DATA:
- Last Price : ${ticker.get('last', 0):,.2f}
- 24h High   : ${ticker.get('high', 0):,.2f}
- 24h Low    : ${ticker.get('low', 0):,.2f}
- Volume     : {ticker.get('volume', 0):,.1f}
- Bid / Ask  : ${ticker.get('bid', 0):,.2f} / ${ticker.get('ask', 0):,.2f}

INDICATORS:
- RSI(14)        : {indicators.get('rsi', 'N/A')}
- MACD           : {indicators.get('macd', 'N/A')}
- MACD Signal    : {indicators.get('macd_signal', 'N/A')}
- MACD Histogram : {indicators.get('macd_hist', 'N/A')}
- BB Upper       : {indicators.get('bb_upper', 'N/A')}
- BB Mid         : {indicators.get('bb_mid', 'N/A')}
- BB Lower       : {indicators.get('bb_lower', 'N/A')}

LAST 5 CANDLES:
{json.dumps(recent_candles, indent=2)}

Respond ONLY with this JSON:
{{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 0-100,
  "reasoning": "2-3 sentences",
  "entry_price": 0.0,
  "stop_loss": 0.0,
  "take_profit": 0.0,
  "risk_score": 1-10,
  "key_factors": ["factor1", "factor2", "factor3"]
}}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.3,
        )

        raw = resp.choices[0].message.content.strip()

        # remove markdown if any
        if "```" in raw:
            raw = raw.split("```")[1].strip()

        result = json.loads(raw)
        result["timestamp"] = datetime.utcnow().isoformat()
        result["pair"] = pair
        return result

    except Exception as e:
        error_msg = str(e)

        # clean error handling (NO leakage to UI)
        if "401" in error_msg or "invalid_api_key" in error_msg:
            user_msg = "AI service unavailable (configuration issue)."
            key_factors = ["API key error"]
        else:
            user_msg = "AI temporarily unavailable. Please try again."
            key_factors = ["System error"]

        return {
            "signal": "HOLD",
            "confidence": 0,
            "risk_score": 5,
            "reasoning": user_msg,
            "entry_price": ticker.get("last", 0),
            "stop_loss": 0,
            "take_profit": 0,
            "key_factors": key_factors,
            "pair": pair,
            "timestamp": datetime.utcnow().isoformat(),
        }


def portfolio_summary(api_key, trades, current_prices):
    """
    Summarize paper trading performance.
    """

    if not trades:
        return "No trades yet."

    client = OpenAI(api_key=api_key)

    prompt = f"""Summarize this paper trading portfolio in 3 sentences.

Trades:
{json.dumps(trades[-20:], indent=2)}

Current prices:
{json.dumps(current_prices)}

Cover: overall PnL, best/worst trade, one suggestion.
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()

    except Exception as e:
        return f"Summary unavailable (AI error)."
