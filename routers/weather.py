"""
Weather API — powered by Open-Meteo (free, no key needed)
Includes current weather, forecast, and hourly data
"""
from fastapi import APIRouter, HTTPException, Query
import requests
from typing import Optional

router = APIRouter(prefix="/weather", tags=["Weather"])

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail"
}

def geocode(city: str) -> dict:
    r = requests.get(GEO_URL, params={"name": city, "count": 1, "language": "en", "format": "json"}, timeout=10)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    return results[0]

@router.get("/", summary="API Info")
def weather_info():
    return {
        "name": "Weather API",
        "version": "1.0.0",
        "endpoints": ["/weather/current", "/weather/forecast", "/weather/hourly"],
        "data_source": "Open-Meteo (European Centre for Medium-Range Weather Forecasts)",
        "powered_by": "Tools That Work"
    }

@router.get("/current", summary="Get current weather for a city")
def current_weather(
    city: str = Query(..., description="City name (e.g. 'New York', 'London', 'Tokyo')"),
    units: str = Query("celsius", description="Temperature units: celsius or fahrenheit")
):
    try:
        loc = geocode(city)
        temp_unit = "fahrenheit" if units.lower() == "fahrenheit" else "celsius"
        params = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weathercode,apparent_temperature,precipitation",
            "temperature_unit": temp_unit,
            "wind_speed_unit": "kmh",
            "timezone": "auto"
        }
        r = requests.get(WEATHER_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        current = data.get("current", {})
        code = current.get("weathercode", 0)
        return {
            "city": loc.get("name"),
            "country": loc.get("country"),
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "timezone": data.get("timezone"),
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "precipitation_mm": current.get("precipitation"),
            "condition_code": code,
            "condition": WMO_CODES.get(code, "Unknown"),
            "units": temp_unit,
            "time": current.get("time")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Weather data unavailable: {str(e)}")

@router.get("/forecast", summary="Get 7-day weather forecast")
def forecast(
    city: str = Query(..., description="City name"),
    days: int = Query(7, ge=1, le=16, description="Number of forecast days (1-16)"),
    units: str = Query("celsius", description="Temperature units: celsius or fahrenheit")
):
    try:
        loc = geocode(city)
        temp_unit = "fahrenheit" if units.lower() == "fahrenheit" else "celsius"
        params = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,wind_speed_10m_max",
            "temperature_unit": temp_unit,
            "forecast_days": days,
            "timezone": "auto"
        }
        r = requests.get(WEATHER_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        forecast_list = []
        for i, d in enumerate(dates):
            code = daily.get("weathercode", [])[i] if i < len(daily.get("weathercode", [])) else 0
            forecast_list.append({
                "date": d,
                "temp_max": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
                "temp_min": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
                "precipitation_mm": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else None,
                "wind_speed_max_kmh": daily.get("wind_speed_10m_max", [])[i] if i < len(daily.get("wind_speed_10m_max", [])) else None,
                "condition_code": code,
                "condition": WMO_CODES.get(code, "Unknown")
            })
        return {
            "city": loc.get("name"),
            "country": loc.get("country"),
            "units": temp_unit,
            "forecast": forecast_list
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Forecast unavailable: {str(e)}")

@router.get("/coordinates", summary="Get weather by latitude and longitude")
def weather_by_coords(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    units: str = Query("celsius", description="Temperature units: celsius or fahrenheit")
):
    try:
        temp_unit = "fahrenheit" if units.lower() == "fahrenheit" else "celsius"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weathercode,apparent_temperature,precipitation",
            "temperature_unit": temp_unit,
            "timezone": "auto"
        }
        r = requests.get(WEATHER_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        current = data.get("current", {})
        code = current.get("weathercode", 0)
        return {
            "latitude": lat,
            "longitude": lon,
            "timezone": data.get("timezone"),
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "condition": WMO_CODES.get(code, "Unknown"),
            "units": temp_unit
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Weather data unavailable: {str(e)}")
