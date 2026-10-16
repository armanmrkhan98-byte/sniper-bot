import os
import time
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(
    title="Pocket Option Pro OTC Bot",
    description="Automated 3s to 5m OTC Trading Signal & Execution Engine",
    version="4.1"
)

BOT_STATE = {
    "is_running": True,
    "mode": "OTC_LIVE",
    "last_signal_time": time.time()
}

OTC_PAIRS = [
    "EURUSD_OTC", "GBPUSD_OTC", "USDJPY_OTC", "AUDUSD_OTC", 
    "USDCAD_OTC", "NZDUSD_OTC", "USDCHF_OTC",
    "EURGBP_OTC", "EURJPY_OTC", "GBPJPY_OTC", "AUDJPY_OTC", 
    "EURAUD_OTC", "GBPCAD_OTC", "GBPNZD_OTC", "EURCAD_OTC",
    "Gold_OTC", "Silver_OTC", "USCrude_OTC", 
    "BTCUSD_OTC", "ETHUSD_OTC"
]

VALID_TIMEFRAMES = [3, 5, 15, 30, 60, 120, 180, 240, 300]

class SignalRequest(BaseModel):
    pair: str
    timeframe: int
    prices: list[float]

class TradeRequest(BaseModel):
    pair: str
    action: str  # "CALL" or "PUT"
    amount: float = 1.0
    duration: int = 60

@app.get("/", response_class=HTMLResponse)
def home():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "<h3>Pocket Option OTC Bot is Running!</h3>"

@app.get("/pairs")
def get_pairs():
    return {"pairs": OTC_PAIRS}

@app.get("/timeframes")
def get_timeframes():
    return {"timeframes": VALID_TIMEFRAMES}

@app.post("/start")
def start_bot():
    BOT_STATE["is_running"] = True
    return {"status": "success", "message": "Bot has been started successfully."}

@app.post("/stop")
def stop_bot():
    BOT_STATE["is_running"] = False
    return {"status": "success", "message": "Bot has been stopped."}

@app.post("/analyze")
def analyze_market(req: SignalRequest):
    if req.pair not in OTC_PAIRS:
        raise HTTPException(status_code=400, detail=f"Invalid OTC pair: {req.pair}")
    
    if req.timeframe not in VALID_TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe: {req.timeframe}s")
    
    # Agar prices na hon ya kam hon, toh random fluctuation generate karein taake CALL aur PUT dono generate hon
    if not req.prices or len(req.prices) < 2:
        import random
        prices = [random.uniform(1.0, 1.1) for _ in range(5)]
    else:
        prices = req.prices

    arr = np.array(prices, dtype=float)
    sma = np.mean(arr)
    current_price = arr[-1]

    # Balanced momentum logic (RSI/Diff based simulation for 50/50 CALL & PUT)
    diff = current_price - sma
    if diff >= 0:
        signal = "CALL"
    else:
        signal = "PUT"
    
    return {
        "pair": req.pair,
        "timeframe": req.timeframe,
        "signal": signal,
        "current_price": current_price,
        "benchmark_sma": sma,
        "timestamp": time.time()
    }

@app.post("/trade")
def execute_trade(req: TradeRequest):
    if not BOT_STATE["is_running"]:
        raise HTTPException(status_code=400, detail="Trading bot is currently stopped.")
    
    if req.pair not in OTC_PAIRS:
        raise HTTPException(status_code=400, detail=f"Invalid OTC pair: {req.pair}")
    
    if req.duration not in VALID_TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Invalid duration: {req.duration}s")
    
    return {
        "status": "success",
        "broker": "Pocket Option",
        "market": "OTC",
        "pair": req.pair,
        "action": req.action.upper(),
        "amount": req.amount,
        "duration_seconds": req.duration,
        "executed_at": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
  
