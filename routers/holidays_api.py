"""
Public Holidays API
Uses the 'holidays' package (offline, 100+ countries)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import holidays
from datetime import date, timedelta

router = APIRouter(prefix="/holidays", tags=["Public Holidays"])

SUPPORTED_COUNTRIES = {
    "AU": "Australia", "AT": "Austria", "BE": "Belgium", "BR": "Brazil",
    "CA": "Canada", "CN": "China", "CO": "Colombia", "HR": "Croatia",
    "CZ": "Czech Republic", "DK": "Denmark", "EG": "Egypt", "FI": "Finland",
    "FR": "France", "DE": "Germany", "GR": "Greece", "HU": "Hungary",
    "IN": "India", "IE": "Ireland", "IL": "Israel", "IT": "Italy",
    "JP": "Japan", "KE": "Kenya", "MX": "Mexico", "MA": "Morocco",
    "NL": "Netherlands", "NZ": "New Zealand", "NG": "Nigeria", "NO": "Norway",
    "PL": "Poland", "PT": "Portugal", "RO": "Romania", "RU": "Russia",
    "ZA": "South Africa", "KR": "South Korea", "ES": "Spain", "SE": "Sweden",
    "CH": "Switzerland", "TW": "Taiwan", "TH": "Thailand", "TN": "Tunisia",
    "TR": "Turkey", "UA": "Ukraine", "GB": "United Kingdom", "US": "United States",
    "VE": "Venezuela", "VN": "Vietnam",
}

@router.get("/", summary="API Info")
def holidays_info():
    return {
        "name": "Public Holidays API",
        "version": "1.0.0",
        "endpoints": ["/holidays/year", "/holidays/today", "/holidays/next", "/holidays/countries"],
        "powered_by": "Tools That Work"
    }

@router.get("/year", summary="Get all public holidays for a country and year")
def get_year(
    country: str = Query(..., description="ISO 2-letter country code (e.g. US, CA, GB, FR, DE)"),
    year: int = Query(None, ge=2000, le=2100, description="Year (default: current year)"),
    state: str = Query(None, description="State/province code for country-specific holidays (e.g. CA for California)")
):
    country = country.upper()
    if country not in SUPPORTED_COUNTRIES:
        raise HTTPException(status_code=400, detail=f"Unsupported country. Use /holidays/countries to see supported ones.")
    if year is None:
        year = date.today().year
    try:
        kwargs = {"years": year}
        if state:
            kwargs["state"] = state.upper()
        h = holidays.country_holidays(country, **kwargs)
        result = sorted([{"date": str(d), "name": name, "weekday": d.strftime("%A")} for d, name in h.items()])
        return {
            "country": SUPPORTED_COUNTRIES[country],
            "country_code": country,
            "year": year,
            "state": state,
            "count": len(result),
            "holidays": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/today", summary="Check if today is a public holiday")
def is_today_holiday(
    country: str = Query(..., description="ISO 2-letter country code"),
):
    country = country.upper()
    if country not in SUPPORTED_COUNTRIES:
        raise HTTPException(status_code=400, detail="Unsupported country")
    today = date.today()
    h = holidays.country_holidays(country, years=today.year)
    is_holiday = today in h
    return {
        "date": str(today),
        "country": SUPPORTED_COUNTRIES[country],
        "is_holiday": is_holiday,
        "holiday_name": h.get(today) if is_holiday else None,
    }

@router.get("/next", summary="Find the next N holidays from today")
def next_holidays(
    country: str = Query(..., description="ISO 2-letter country code"),
    count: int = Query(5, ge=1, le=20, description="Number of upcoming holidays to return")
):
    country = country.upper()
    if country not in SUPPORTED_COUNTRIES:
        raise HTTPException(status_code=400, detail="Unsupported country")
    today = date.today()
    h = holidays.country_holidays(country, years=[today.year, today.year + 1])
    upcoming = sorted([(d, name) for d, name in h.items() if d >= today])[:count]
    return {
        "country": SUPPORTED_COUNTRIES[country],
        "from_date": str(today),
        "holidays": [{"date": str(d), "name": name, "days_away": (d - today).days, "weekday": d.strftime("%A")} for d, name in upcoming]
    }

@router.get("/countries", summary="List all supported countries")
def list_countries():
    return {"countries": [{"code": k, "name": v} for k, v in sorted(SUPPORTED_COUNTRIES.items(), key=lambda x: x[1])], "count": len(SUPPORTED_COUNTRIES)}
