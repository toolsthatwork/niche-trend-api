"""
Crypto & Token Price API
Uses CoinGecko free API (no key needed for basic endpoints)
"""
from fastapi import APIRouter, HTTPException, Query
import requests
from typing import Optional

router = APIRouter(prefix="/crypto", tags=["Crypto & Token Prices"])

BASE = "https://api.coingecko.com/api/v3"
HEADERS = {"accept": "application/json"}

@router.get("/", summary="API Info")
def crypto_info():
    return {
        "name": "Crypto & Token Price API",
        "version": "1.0.0",
        "endpoints": ["/crypto/price", "/crypto/trending", "/crypto/top", "/crypto/history"],
        "data_source": "CoinGecko",
        "powered_by": "Tools That Work"
    }

@router.get("/price", summary="Get current price for one or more cryptocurrencies")
def get_price(
    coins: str = Query(..., description="Comma-separated coin IDs (e.g. bitcoin,ethereum,solana)"),
    vs_currencies: str = Query("usd", description="Comma-separated currencies (e.g. usd,eur,cad)")
):
    try:
        r = requests.get(f"{BASE}/simple/price", headers=HEADERS, params={
            "ids": coins.lower(),
            "vs_currencies": vs_currencies.lower(),
            "include_24hr_change": True,
            "include_market_cap": True,
            "include_24hr_vol": True
        }, timeout=15)
        r.raise_for_status()
        return {"prices": r.json(), "currencies": vs_currencies.split(",")}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Price data unavailable: {str(e)}")

@router.get("/trending", summary="Get top 7 trending coins on CoinGecko")
def trending_coins():
    try:
        r = requests.get(f"{BASE}/search/trending", headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        coins = []
        for item in data.get("coins", []):
            coin = item.get("item", {})
            coins.append({
                "id": coin.get("id"),
                "name": coin.get("name"),
                "symbol": coin.get("symbol"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "score": coin.get("score")
            })
        return {"trending": coins, "count": len(coins)}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Trending data unavailable: {str(e)}")

@router.get("/top", summary="Get top N cryptocurrencies by market cap")
def top_coins(
    limit: int = Query(10, ge=1, le=100, description="Number of coins (1-100)"),
    vs_currency: str = Query("usd", description="Target currency"),
    order: str = Query("market_cap_desc", description="Sort order: market_cap_desc, volume_desc, gecko_desc")
):
    try:
        r = requests.get(f"{BASE}/coins/markets", headers=HEADERS, params={
            "vs_currency": vs_currency,
            "order": order,
            "per_page": limit,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h"
        }, timeout=15)
        r.raise_for_status()
        coins = []
        for coin in r.json():
            coins.append({
                "rank": coin.get("market_cap_rank"),
                "id": coin.get("id"),
                "symbol": coin.get("symbol"),
                "name": coin.get("name"),
                "price": coin.get("current_price"),
                "market_cap": coin.get("market_cap"),
                "volume_24h": coin.get("total_volume"),
                "change_24h_pct": coin.get("price_change_percentage_24h"),
                "ath": coin.get("ath"),
                "currency": vs_currency
            })
        return {"coins": coins, "count": len(coins), "currency": vs_currency}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Market data unavailable: {str(e)}")

@router.get("/history", summary="Get historical price for a coin")
def coin_history(
    coin_id: str = Query(..., description="CoinGecko coin ID (e.g. bitcoin, ethereum)"),
    days: int = Query(7, ge=1, le=365, description="Number of days of history"),
    vs_currency: str = Query("usd", description="Target currency")
):
    try:
        r = requests.get(f"{BASE}/coins/{coin_id}/market_chart", headers=HEADERS, params={
            "vs_currency": vs_currency,
            "days": days
        }, timeout=15)
        r.raise_for_status()
        data = r.json()
        prices = [[p[0], p[1]] for p in data.get("prices", [])]
        return {
            "coin_id": coin_id,
            "currency": vs_currency,
            "days": days,
            "data_points": len(prices),
            "prices": prices  # [timestamp_ms, price]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"History unavailable: {str(e)}")
