"""
Country Information API
Uses restcountries.com (free, no key needed)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
import requests

router = APIRouter(prefix="/country", tags=["Country Information"])
BASE = "https://restcountries.com/v3.1"

def simplify(c: dict) -> dict:
    return {
        "name": c.get("name", {}).get("common"),
        "official_name": c.get("name", {}).get("official"),
        "cca2": c.get("cca2"),
        "cca3": c.get("cca3"),
        "capital": c.get("capital", [None])[0],
        "region": c.get("region"),
        "subregion": c.get("subregion"),
        "population": c.get("population"),
        "area_km2": c.get("area"),
        "languages": list(c.get("languages", {}).values()),
        "currencies": [
            {"code": k, "name": v.get("name"), "symbol": v.get("symbol")}
            for k, v in c.get("currencies", {}).items()
        ],
        "timezones": c.get("timezones", []),
        "calling_code": [f"+{d}" for d in c.get("idd", {}).get("suffixes", []) if c.get("idd", {}).get("root")],
        "tld": c.get("tld", []),
        "flag_emoji": c.get("flag"),
        "flags": c.get("flags", {}).get("svg"),
        "landlocked": c.get("landlocked"),
        "borders": c.get("borders", []),
        "driving_side": c.get("car", {}).get("side"),
        "continents": c.get("continents", []),
        "lat_lng": c.get("latlng"),
        "un_member": c.get("unMember"),
        "independent": c.get("independent"),
    }

@router.get("/", summary="API Info")
def country_info():
    return {
        "name": "Country Information API",
        "version": "1.0.0",
        "endpoints": ["/country/name", "/country/code", "/country/all", "/country/region", "/country/search"],
        "powered_by": "Tools That Work"
    }

@router.get("/name", summary="Get country by name")
def by_name(
    name: str = Query(..., description="Country name (e.g. France, Germany, Brazil)"),
    full: bool = Query(False, description="Exact match only")
):
    try:
        r = requests.get(f"{BASE}/name/{name}", params={"fullText": str(full).lower()}, timeout=10)
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Country not found: {name}")
        r.raise_for_status()
        return {"results": [simplify(c) for c in r.json()[:5]]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/code", summary="Get country by ISO code (2 or 3 letter)")
def by_code(
    code: str = Query(..., description="ISO 3166-1 alpha-2 or alpha-3 code (e.g. US, FRA, CA)")
):
    try:
        r = requests.get(f"{BASE}/alpha/{code.upper()}", timeout=10)
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Country not found: {code}")
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return simplify(data[0])
        return simplify(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/region", summary="Get all countries in a region")
def by_region(
    region: str = Query(..., description="Region: Africa, Americas, Asia, Europe, Oceania, Antarctic")
):
    try:
        r = requests.get(f"{BASE}/region/{region}", timeout=10)
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Region not found: {region}")
        r.raise_for_status()
        countries = sorted(r.json(), key=lambda c: c.get("name", {}).get("common", ""))
        return {"region": region, "count": len(countries), "countries": [simplify(c) for c in countries]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/all", summary="Get all countries (basic info)")
def all_countries():
    try:
        r = requests.get(f"{BASE}/all?fields=name,cca2,cca3,flag,region,population", timeout=15)
        r.raise_for_status()
        countries = sorted(r.json(), key=lambda c: c.get("name", {}).get("common", ""))
        return {
            "count": len(countries),
            "countries": [
                {
                    "name": c.get("name", {}).get("common"),
                    "cca2": c.get("cca2"),
                    "cca3": c.get("cca3"),
                    "flag": c.get("flag"),
                    "region": c.get("region"),
                    "population": c.get("population"),
                } for c in countries
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
