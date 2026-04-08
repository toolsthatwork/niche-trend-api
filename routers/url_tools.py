"""
URL Tools API
Redirect tracer, unshortener, status checker — uses requests (free)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
import requests
from urllib.parse import urlparse

router = APIRouter(prefix="/url", tags=["URL Tools"])

def is_valid_url(url: str) -> bool:
    try:
        r = urlparse(url)
        return r.scheme in ("http", "https") and bool(r.netloc)
    except Exception:
        return False

@router.get("/", summary="API Info")
def url_info():
    return {
        "name": "URL Tools API",
        "version": "1.0.0",
        "endpoints": ["/url/trace", "/url/status", "/url/parse", "/url/bulk/status"],
        "powered_by": "Tools That Work"
    }

@router.get("/trace", summary="Trace redirects for a URL (unshorten)")
def trace_redirects(
    url: str = Query(..., description="URL to trace (e.g. a shortened URL)"),
    max_redirects: int = Query(10, ge=1, le=20, description="Max redirects to follow")
):
    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL. Must start with http:// or https://")
    try:
        session = requests.Session()
        session.max_redirects = max_redirects
        resp = session.head(url, allow_redirects=True, timeout=10,
                            headers={"User-Agent": "Mozilla/5.0"})
        chain = []
        for r in resp.history:
            chain.append({
                "url": r.url,
                "status_code": r.status_code,
                "redirect_to": r.headers.get("Location")
            })
        chain.append({"url": resp.url, "status_code": resp.status_code, "redirect_to": None})
        return {
            "original_url": url,
            "final_url": resp.url,
            "redirects": len(resp.history),
            "chain": chain,
            "shortened": url != resp.url
        }
    except requests.TooManyRedirects:
        raise HTTPException(status_code=400, detail=f"Too many redirects (>{max_redirects})")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not trace URL: {str(e)}")

@router.get("/status", summary="Check HTTP status of a URL")
def check_status(
    url: str = Query(..., description="URL to check"),
    follow_redirects: bool = Query(True, description="Follow redirects")
):
    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    try:
        resp = requests.head(url, allow_redirects=follow_redirects, timeout=10,
                             headers={"User-Agent": "Mozilla/5.0"})
        return {
            "url": url,
            "final_url": resp.url,
            "status_code": resp.status_code,
            "status_text": requests.status_codes._codes.get(resp.status_code, ["Unknown"])[0].upper().replace("_", " "),
            "online": 200 <= resp.status_code < 400,
            "content_type": resp.headers.get("Content-Type"),
            "server": resp.headers.get("Server"),
            "response_time_ms": int(resp.elapsed.total_seconds() * 1000),
        }
    except requests.ConnectionError:
        return {"url": url, "status_code": None, "online": False, "error": "Connection refused or DNS failed"}
    except requests.Timeout:
        return {"url": url, "status_code": None, "online": False, "error": "Request timed out"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/parse", summary="Parse and analyze a URL")
def parse_url(
    url: str = Query(..., description="URL to parse")
):
    try:
        parsed = urlparse(url)
        return {
            "url": url,
            "scheme": parsed.scheme,
            "domain": parsed.netloc,
            "path": parsed.path or "/",
            "query": parsed.query or None,
            "fragment": parsed.fragment or None,
            "username": parsed.username,
            "password": "***" if parsed.password else None,
            "port": parsed.port,
            "tld": ".".join(parsed.netloc.split(".")[-2:]) if "." in parsed.netloc else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class BulkStatusRequest(BaseModel):
    urls: List[str]

@router.post("/bulk/status", summary="Check status of multiple URLs (max 20)")
def bulk_status(req: BulkStatusRequest):
    if len(req.urls) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 URLs per request")
    results = []
    for url in req.urls:
        if not is_valid_url(url):
            results.append({"url": url, "online": False, "error": "Invalid URL"})
            continue
        try:
            resp = requests.head(url, allow_redirects=True, timeout=8,
                                 headers={"User-Agent": "Mozilla/5.0"})
            results.append({
                "url": url,
                "status_code": resp.status_code,
                "online": 200 <= resp.status_code < 400,
                "response_time_ms": int(resp.elapsed.total_seconds() * 1000)
            })
        except Exception as e:
            results.append({"url": url, "online": False, "error": str(e)})
    return {"results": results, "count": len(results)}
