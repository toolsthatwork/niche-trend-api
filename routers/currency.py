"""
Currency & Forex Exchange API
Powered by Frankfurter (ECB data, free, no key needed)
"""
from fastapi import APIRouter, HTTPException, Query
import requests
from datetime import date, timedelta
from typing import Optional

router = APIRouter(prefix="/currency", tags=["Currency & Forex"])

BASE = "https://api.frankfurter.app"

SUPPORTED_CURRENCIES = [
    "USD","EUR","GBP","CAD","AUD","JPY","CHF","CNY","INR","MXN",
    "BRL","KRW","SGD","HKD","NOK","SEK","DKK","NZD","ZAR","RUB"
]

@router.get("/", summary="API Info")
def currency_info():
    return {
        "name": "Currency & Forex Exchange API",
        "version": "1.0.0",
        "endpoints": ["/currency/latest", "/currency/convert", "/currency/historical", "/currency/currencies"],
        "powered_by": "Tools That Work"
    }

@router.get("/currencies", summary="List all supported currencies")
def list_currencies():
    try:
        r = requests.get(f"{BASE}/currencies", timeout=10)
        r.raise_for_status()
        return {"currencies": r.json(), "count": len(r.json())}
    except Exception:
        return {"currencies": {c: c for c in SUPPORTED_CURRENCIES}, "count": len(SUPPORTED_CURRENCIES)}

@router.get("/latest", summary="Get latest exchange rates")
def latest_rates(
    base: str = Query("USD", description="Base currency (e.g. USD, EUR, GBP)"),
    symbols: Optional[str] = Query(None, description="Comma-separated target currencies (e.g. EUR,GBP,CAD)")
):
    params = {"from": base.upper()}
    if symbols:
        params["to"] = symbols.upper()
    try:
        r = requests.get(f"{BASE}/latest", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "base": data.get("base"),
            "date": data.get("date"),
            "rates": data.get("rates"),
            "source": "European Central Bank"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Currency data unavailable: {str(e)}")

@router.get("/convert", summary="Convert an amount between currencies")
def convert(
    amount: float = Query(..., description="Amount to convert"),
    from_currency: str = Query("USD", alias="from", description="Source currency"),
    to_currency: str = Query("EUR", alias="to", description="Target currency")
):
    params = {"amount": amount, "from": from_currency.upper(), "to": to_currency.upper()}
    try:
        r = requests.get(f"{BASE}/latest", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        result = list(data.get("rates", {}).values())[0] if data.get("rates") else None
        return {
            "from": from_currency.upper(),
            "to": to_currency.upper(),
            "amount": amount,
            "result": result,
            "date": data.get("date"),
            "rate": result / amount if result and amount else None
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Conversion failed: {str(e)}")

@router.get("/historical", summary="Get historical exchange rates")
def historical(
    date_str: str = Query(..., alias="date", description="Date in YYYY-MM-DD format"),
    base: str = Query("USD", description="Base currency"),
    symbols: Optional[str] = Query(None, description="Comma-separated target currencies")
):
    params = {"from": base.upper()}
    if symbols:
        params["to"] = symbols.upper()
    try:
        r = requests.get(f"{BASE}/{date_str}", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "base": data.get("base"),
            "date": data.get("date"),
            "rates": data.get("rates"),
            "source": "European Central Bank"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Historical data unavailable: {str(e)}")

@router.get("/range", summary="Get exchange rates over a date range")
def rate_range(
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
    base: str = Query("USD", description="Base currency"),
    symbols: Optional[str] = Query(None, description="Comma-separated target currencies")
):
    params = {"from": base.upper()}
    if symbols:
        params["to"] = symbols.upper()
    try:
        r = requests.get(f"{BASE}/{start_date}..{end_date}", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "base": data.get("base"),
            "start_date": start_date,
            "end_date": end_date,
            "rates": data.get("rates"),
            "source": "European Central Bank"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Range data unavailable: {str(e)}")
