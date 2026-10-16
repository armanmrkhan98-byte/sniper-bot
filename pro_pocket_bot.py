import pandas as pd
import numpy as np
import talib
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class ProMarketSignalEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def analyze_advanced_indicators(self) -> Dict[str, Any]:
        close = self.df['close'].values
        open_p = self.df['open'].values
        high = self.df['high'].values
        low = self.df['low'].values

        # Indicators
        rsi = talib.RSI(close, timeperiod=14)
        ema_9 = talib.EMA(close, timeperiod=9)
        ema_21 = talib.EMA(close, timeperiod=21)
        ema_50 = talib.EMA(close, timeperiod=50)
        
        # MACD for Momentum
        macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

        # Candlestick Patterns
        engulfing = talib.CDLENGULFING(open_p, high, low, close)
        hammer = talib.CDLHAMMER(open_p, high, low, close)
        shooting_star = talib.CDLSHOOTINGSTAR(open_p, high, low, close)
        morning_star = talib.CDLMORNINGSTAR(open_p, high, low, close)
        evening_star = talib.CDLEVENINGSTAR(open_p, high, low, close)

        return {
            "rsi": rsi[-1],
            "ema_9": ema_9[-1],
            "ema_21": ema_21[-1],
            "ema_50": ema_50[-1],
            "macd_hist": macd_hist[-1],
            "engulfing": engulfing[-1],
            "hammer": hammer[-1],
            "shooting_star": shooting_star[-1],
            "morning_star": morning_star[-1],
            "evening_star": evening_star[-1]
        }

    def generate_high_probability_signal(self) -> Dict[str, Any]:
        data = self.analyze_advanced_indicators()
        
        rsi = data["rsi"]
        ema_9 = data["ema_9"]
        ema_21 = data["ema_21"]
        ema_50 = data["ema_50"]
        macd_hist = data["macd_hist"]

        decision = "HOLD"
        score = 0  # Confidence score builder
        reasons = []

        # --- Trend Direction ---
        uptrend = ema_9 > ema_21 > ema_50
        downtrend = ema_9 < ema_21 < ema_50

        # --- CALL (BUY) STRICT CONDITIONS ---
        if uptrend:
            score += 35
            reasons.append("Strong Uptrend (EMA alignment)")
            
        if data["engulfing"] == 100 or data["hammer"] == 100 or data["morning_star"] > 0:
            score += 30
            reasons.append("Bullish Reversal Pattern detected")
            
        if 40 <= rsi <= 65:  # Healthy uptrend zone, not overbought yet
            score += 20
            reasons.append("RSI in healthy bullish zone")
            
        if macd_hist > 0:
            score += 15
            reasons.append("MACD momentum positive")

        # Execution check for CALL
        if score >= 85 and uptrend:
            return {"action": "CALL", "confidence_score": f"{score}%", "reasons": reasons}

        # Reset score for PUT evaluation
        score = 0
        reasons = []

        # --- PUT (SELL) STRICT CONDITIONS ---
        if downtrend:
            score += 35
            reasons.append("Strong Downtrend (EMA alignment)")
            
        if data["engulfing"] == -100 or data["shooting_star"] == -100 or data["evening_star"] < 0:
            score += 30
            reasons.append("Bearish Reversal Pattern detected")
            
        if 35 <= rsi <= 60:  # Healthy downtrend zone, not oversold yet
            score += 20
            reasons.append("RSI in healthy bearish zone")
            
        if macd_hist < 0:
            score += 15
            reasons.append("MACD momentum negative")

        # Execution check for PUT
        if score >= 85 and downtrend:
            return {"action": "PUT", "confidence_score": f"{score}%", "reasons": reasons}

        return {"action": "HOLD", "confidence_score": f"{score}%", "reasons": ["Market conditions not optimal or mixed signals"]}

app = FastAPI(title="Pro Pocket Option High-Accuracy Signal API")

class Candle(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketData(BaseModel):
    symbol: str
    is_otc: bool
    candles: List[Candle]

@app.post("/pro-analyze")
async def pro_analyze(data: MarketData):
    if len(data.candles) < 50:
        raise HTTPException(status_code=400, detail="Minimum 50 candles required for advanced analysis.")

    df = pd.DataFrame([c.dict() for c in data.candles])
    engine = ProMarketSignalEngine(df)
    result = engine.generate_high_probability_signal()
    result["symbol"] = data.symbol
    result["is_otc"] = data.is_otc

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
          
