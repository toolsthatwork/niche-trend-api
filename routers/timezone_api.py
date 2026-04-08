"""
Timezone API
Uses pytz (offline) + datetime
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import pytz

router = APIRouter(prefix="/timezone", tags=["Timezone"])

@router.get("/", summary="API Info")
def timezone_info():
    return {
        "name": "Timezone API",
        "version": "1.0.0",
        "endpoints": ["/timezone/now", "/timezone/convert", "/timezone/list", "/timezone/info"],
        "powered_by": "Tools That Work"
    }

@router.get("/now", summary="Get current time in a timezone")
def current_time(
    tz: str = Query(..., description="Timezone (e.g. America/New_York, Europe/Paris, Asia/Tokyo)")
):
    try:
        zone = pytz.timezone(tz)
    except pytz.UnknownTimeZoneError:
        raise HTTPException(status_code=400, detail=f"Unknown timezone: {tz}. Use /timezone/list to see valid zones.")
    now = datetime.now(zone)
    utc_now = datetime.now(pytz.utc)
    offset = now.utcoffset()
    offset_hours = offset.total_seconds() / 3600 if offset else 0
    return {
        "timezone": tz,
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": now.strftime("%A"),
        "utc_offset": f"{'+' if offset_hours >= 0 else ''}{offset_hours:.1f}",
        "utc_offset_seconds": int(offset.total_seconds()) if offset else 0,
        "is_dst": bool(now.dst()),
        "abbreviation": now.strftime("%Z"),
        "unix_timestamp": int(now.timestamp()),
    }

@router.get("/convert", summary="Convert time between timezones")
def convert_time(
    datetime_str: str = Query(..., description="Datetime in ISO format (e.g. 2024-06-15 14:30:00)"),
    from_tz: str = Query(..., description="Source timezone (e.g. America/New_York)"),
    to_tz: str = Query(..., description="Target timezone (e.g. Asia/Tokyo)")
):
    try:
        src_zone = pytz.timezone(from_tz)
    except pytz.UnknownTimeZoneError:
        raise HTTPException(status_code=400, detail=f"Unknown source timezone: {from_tz}")
    try:
        dst_zone = pytz.timezone(to_tz)
    except pytz.UnknownTimeZoneError:
        raise HTTPException(status_code=400, detail=f"Unknown target timezone: {to_tz}")
    try:
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        src_dt = src_zone.localize(dt)
        dst_dt = src_dt.astimezone(dst_zone)
        return {
            "original": {"datetime": datetime_str, "timezone": from_tz},
            "converted": {
                "datetime": dst_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": to_tz,
                "abbreviation": dst_dt.strftime("%Z"),
            },
            "difference_hours": (dst_dt.utcoffset() - src_dt.utcoffset()).total_seconds() / 3600
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use: YYYY-MM-DD HH:MM:SS")

@router.get("/info", summary="Get info about a timezone")
def timezone_details(
    tz: str = Query(..., description="Timezone name (e.g. America/New_York)")
):
    try:
        zone = pytz.timezone(tz)
    except pytz.UnknownTimeZoneError:
        raise HTTPException(status_code=400, detail=f"Unknown timezone: {tz}")
    now = datetime.now(zone)
    offset = now.utcoffset()
    offset_hours = offset.total_seconds() / 3600 if offset else 0
    return {
        "timezone": tz,
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "utc_offset": f"{'+' if offset_hours >= 0 else ''}{offset_hours:.1f}",
        "utc_offset_seconds": int(offset.total_seconds()) if offset else 0,
        "abbreviation": now.strftime("%Z"),
        "is_dst": bool(now.dst()),
        "country": tz.split("/")[0] if "/" in tz else None,
        "city": tz.split("/")[-1].replace("_", " ") if "/" in tz else tz,
    }

@router.get("/list", summary="List all available timezones")
def list_timezones(
    region: str = Query(None, description="Filter by region: America, Europe, Asia, Africa, Pacific, Australia, Atlantic, Indian, Arctic, Antarctica")
):
    zones = list(pytz.all_timezones)
    if region:
        zones = [z for z in zones if z.startswith(region)]
    return {"timezones": zones, "count": len(zones)}
