"""
Stock Prices API
Uses yfinance (Yahoo Finance — free, no key needed)
"""
from fastapi import APIRouter, HTTPException, Query
import yfinance as yf
from typing import Optional

router = APIRouter(prefix="/stocks", tags=["Stock Prices"])

@router.get("/", summary="API Info")
def stocks_info():
    return {
        "name": "Stock Prices API",
        "version": "1.0.0",
        "endpoints": ["/stocks/quote", "/stocks/history", "/stocks/info", "/stocks/search"],
        "data_source": "Yahoo Finance (via yfinance)",
        "powered_by": "Tools That Work"
    }

@router.get("/quote", summary="Get real-time stock quote")
def get_quote(
    symbol: str = Query(..., description="Stock ticker symbol (e.g. AAPL, TSLA, MSFT)"),
):
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.fast_info
        return {
            "symbol": symbol.upper(),
            "price": info.last_price,
            "previous_close": info.previous_close,
            "open": info.open,
            "day_high": info.day_high,
            "day_low": info.day_low,
            "volume": info.last_volume,
            "market_cap": getattr(info, "market_cap", None),
            "currency": getattr(info, "currency", "USD"),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Quote unavailable: {str(e)}")

@router.get("/info", summary="Get detailed stock info and fundamentals")
def get_info(
    symbol: str = Query(..., description="Stock ticker symbol"),
):
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        keys = ["shortName", "sector", "industry", "country", "website",
                "marketCap", "trailingPE", "forwardPE", "dividendYield",
                "52WeekChange", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
                "averageVolume", "beta", "earningsGrowth", "revenueGrowth",
                "grossMargins", "operatingMargins", "profitMargins"]
        return {k: info.get(k) for k in keys if info.get(k) is not None}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Info unavailable: {str(e)}")

@router.get("/history", summary="Get historical price data")
def get_history(
    symbol: str = Query(..., description="Stock ticker symbol"),
    period: str = Query("1mo", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"),
    interval: str = Query("1d", description="Interval: 1m, 5m, 15m, 1h, 1d, 1wk, 1mo")
):
    try:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            raise HTTPException(status_code=404, detail="No data found for symbol")
        records = []
        for ts, row in hist.iterrows():
            records.append({
                "date": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "open": round(float(row["Open"]), 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(float(row["Close"]), 4),
                "volume": int(row["Volume"]),
            })
        return {"symbol": symbol.upper(), "period": period, "interval": interval,
                "count": len(records), "data": records}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"History unavailable: {str(e)}")

@router.get("/multi", summary="Get quotes for multiple symbols")
def get_multi(
    symbols: str = Query(..., description="Comma-separated ticker symbols (e.g. AAPL,MSFT,GOOG)"),
):
    try:
        result = []
        for sym in [s.strip().upper() for s in symbols.split(",")][:20]:
            try:
                info = yf.Ticker(sym).fast_info
                result.append({
                    "symbol": sym,
                    "price": info.last_price,
                    "previous_close": info.previous_close,
                    "change_pct": round(((info.last_price - info.previous_close) / info.previous_close) * 100, 2)
                    if info.previous_close else None,
                })
            except Exception:
                result.append({"symbol": sym, "error": "Not found"})
        return {"quotes": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
