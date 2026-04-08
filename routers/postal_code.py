"""
Postal Code Lookup API
Uses zippopotam.us (free, no key)
"""
from fastapi import APIRouter, HTTPException, Query
import requests

router = APIRouter(prefix="/postal", tags=["Postal Code Lookup"])
BASE = "http://api.zippopotam.us"

@router.get("/", summary="API Info")
def postal_info():
    return {
        "name": "Postal Code Lookup API",
        "version": "1.0.0",
        "endpoints": ["/postal/lookup", "/postal/city"],
        "data_source": "Zippopotam.us",
        "powered_by": "Tools That Work"
    }

@router.get("/lookup", summary="Look up location by postal code")
def lookup_postal(
    country: str = Query(..., description="ISO 2-letter country code (e.g. US, CA, GB, DE, FR)"),
    code: str = Query(..., description="Postal/ZIP code (e.g. 90210, SW1A 1AA)")
):
    country = country.upper().strip()
    code = code.strip()
    try:
        r = requests.get(f"{BASE}/{country}/{code}", timeout=10)
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Postal code '{code}' not found in {country}")
        r.raise_for_status()
        data = r.json()
        places = []
        for place in data.get("places", []):
            places.append({
                "place_name": place.get("place name"),
                "state": place.get("state"),
                "state_code": place.get("state abbreviation"),
                "latitude": float(place.get("latitude", 0)),
                "longitude": float(place.get("longitude", 0)),
            })
        return {
            "postal_code": data.get("post code"),
            "country": data.get("country"),
            "country_code": data.get("country abbreviation"),
            "places": places,
            "count": len(places)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Lookup failed: {str(e)}")

@router.get("/city", summary="Look up postal codes by city and state")
def lookup_city(
    country: str = Query(..., description="ISO 2-letter country code (e.g. US, CA)"),
    state: str = Query(..., description="State/province code (e.g. CA, NY, ON)"),
    city: str = Query(..., description="City name (e.g. Beverly Hills)")
):
    country = country.upper().strip()
    state = state.upper().strip()
    try:
        r = requests.get(f"{BASE}/{country}/{state}/{city}", timeout=10)
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"City '{city}' not found in {state}, {country}")
        r.raise_for_status()
        data = r.json()
        places = []
        for place in data.get("places", []):
            places.append({
                "postal_code": place.get("post code"),
                "place_name": place.get("place name"),
                "latitude": float(place.get("latitude", 0)),
                "longitude": float(place.get("longitude", 0)),
            })
        return {
            "city": city,
            "state": state,
            "country": data.get("country"),
            "places": places,
            "count": len(places)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Lookup failed: {str(e)}")
