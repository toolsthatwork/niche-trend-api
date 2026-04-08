"""
IP Geolocation API
Uses ip-api.com (free, no key needed, 45 req/min)
"""
from fastapi import APIRouter, HTTPException, Query, Request
import requests
from typing import Optional

router = APIRouter(prefix="/ip", tags=["IP Geolocation"])

IP_API = "http://ip-api.com/json"
FIELDS = "status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query,mobile,proxy,hosting"

@router.get("/", summary="API Info")
def ip_info():
    return {
        "name": "IP Geolocation API",
        "version": "1.0.0",
        "endpoints": ["/ip/lookup", "/ip/me", "/ip/bulk"],
        "powered_by": "Tools That Work"
    }

@router.get("/lookup", summary="Look up geolocation for an IP address")
def lookup_ip(
    ip: str = Query(..., description="IPv4 or IPv6 address to look up"),
    lang: str = Query("en", description="Response language (en, de, es, pt-BR, fr, ja, zh-CN, ru)")
):
    try:
        params = {"fields": FIELDS, "lang": lang}
        r = requests.get(f"{IP_API}/{ip}", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "fail":
            raise HTTPException(status_code=400, detail=data.get("message", "Invalid IP address"))
        return {
            "ip": data.get("query"),
            "country": data.get("country"),
            "country_code": data.get("countryCode"),
            "region": data.get("regionName"),
            "region_code": data.get("region"),
            "city": data.get("city"),
            "zip": data.get("zip"),
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
            "timezone": data.get("timezone"),
            "isp": data.get("isp"),
            "organization": data.get("org"),
            "as": data.get("as"),
            "is_mobile": data.get("mobile"),
            "is_proxy": data.get("proxy"),
            "is_hosting": data.get("hosting")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"IP lookup failed: {str(e)}")

@router.get("/me", summary="Get geolocation for the caller's IP address")
def my_ip(request: Request):
    ip = request.client.host
    # Check for forwarded IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    try:
        params = {"fields": FIELDS}
        r = requests.get(f"{IP_API}/{ip}", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "ip": data.get("query"),
            "country": data.get("country"),
            "country_code": data.get("countryCode"),
            "region": data.get("regionName"),
            "city": data.get("city"),
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
            "timezone": data.get("timezone"),
            "isp": data.get("isp"),
            "is_proxy": data.get("proxy")
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"IP lookup failed: {str(e)}")

@router.post("/bulk", summary="Look up multiple IP addresses (max 50)")
def bulk_lookup(ips: list[str]):
    if len(ips) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 IPs per request")
    results = []
    for ip in ips:
        try:
            r = requests.get(f"{IP_API}/{ip}", params={"fields": FIELDS}, timeout=10)
            data = r.json()
            results.append({
                "ip": ip,
                "country": data.get("country"),
                "country_code": data.get("countryCode"),
                "city": data.get("city"),
                "latitude": data.get("lat"),
                "longitude": data.get("lon"),
                "timezone": data.get("timezone"),
                "is_proxy": data.get("proxy"),
                "status": data.get("status")
            })
        except Exception:
            results.append({"ip": ip, "status": "error"})
    return {"total": len(ips), "results": results}
