"""
SSL Certificate Checker API
Uses Python's built-in ssl + socket modules (offline, no external deps)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
import ssl
import socket
from datetime import datetime, timezone

router = APIRouter(prefix="/ssl", tags=["SSL Certificate Checker"])

def check_ssl(hostname: str, port: int = 443) -> dict:
    hostname = hostname.replace("https://", "").replace("http://", "").split("/")[0]
    try:
        ctx = ssl.create_default_context()
        conn = ctx.wrap_socket(socket.create_connection((hostname, port), timeout=10), server_hostname=hostname)
        cert = conn.getpeercert()
        conn.close()

        # Parse dates
        not_before = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days_left = (not_after - now).days

        # Extract SANs
        sans = []
        for entry in cert.get("subjectAltName", []):
            if entry[0] == "DNS":
                sans.append(entry[1])

        # Extract issuer
        issuer = dict(x[0] for x in cert.get("issuer", []))
        subject = dict(x[0] for x in cert.get("subject", []))

        return {
            "hostname": hostname,
            "port": port,
            "valid": True,
            "expired": now > not_after,
            "days_until_expiry": days_left,
            "not_before": not_before.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "not_after": not_after.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "subject": {
                "common_name": subject.get("commonName"),
                "organization": subject.get("organizationName"),
                "country": subject.get("countryName"),
            },
            "issuer": {
                "common_name": issuer.get("commonName"),
                "organization": issuer.get("organizationName"),
                "country": issuer.get("countryName"),
            },
            "sans": sans,
            "version": cert.get("version"),
            "serial_number": cert.get("serialNumber"),
            "status": "VALID" if not now > not_after and days_left > 0 else "EXPIRED",
            "warning": "Expires soon!" if 0 < days_left <= 30 else None,
        }
    except ssl.SSLCertVerificationError as e:
        return {"hostname": hostname, "port": port, "valid": False, "error": f"SSL verification failed: {str(e)}"}
    except ssl.SSLError as e:
        return {"hostname": hostname, "port": port, "valid": False, "error": f"SSL error: {str(e)}"}
    except socket.timeout:
        return {"hostname": hostname, "port": port, "valid": False, "error": "Connection timed out"}
    except socket.gaierror:
        return {"hostname": hostname, "port": port, "valid": False, "error": "DNS resolution failed"}
    except ConnectionRefusedError:
        return {"hostname": hostname, "port": port, "valid": False, "error": "Connection refused"}
    except Exception as e:
        return {"hostname": hostname, "port": port, "valid": False, "error": str(e)}

class BulkRequest(BaseModel):
    domains: List[str]
    port: int = 443

@router.get("/", summary="API Info")
def ssl_info():
    return {
        "name": "SSL Certificate Checker API",
        "version": "1.0.0",
        "endpoints": ["/ssl/check", "/ssl/bulk", "/ssl/expiry"],
        "powered_by": "Tools That Work"
    }

@router.get("/check", summary="Check SSL certificate for a domain")
def ssl_check(
    domain: str = Query(..., description="Domain to check (e.g. google.com or https://google.com)"),
    port: int = Query(443, ge=1, le=65535, description="Port (default: 443)")
):
    return check_ssl(domain, port)

@router.get("/expiry", summary="Quick check — days until SSL certificate expires")
def ssl_expiry(domain: str = Query(..., description="Domain to check")):
    result = check_ssl(domain)
    if not result.get("valid"):
        return result
    return {
        "domain": result["hostname"],
        "days_until_expiry": result["days_until_expiry"],
        "expires_on": result["not_after"],
        "status": result["status"],
        "warning": result.get("warning"),
    }

@router.post("/bulk", summary="Check SSL for multiple domains (max 20)")
def ssl_bulk(req: BulkRequest):
    if len(req.domains) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 domains per request")
    results = [check_ssl(d, req.port) for d in req.domains]
    return {
        "results": results,
        "count": len(results),
        "valid_count": sum(1 for r in results if r.get("valid")),
        "expired_count": sum(1 for r in results if r.get("expired")),
    }
