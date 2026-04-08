"""
Domain & WHOIS Lookup API
Uses python-whois (free, no API key)
"""
from fastapi import APIRouter, HTTPException, Query
import whois
import socket
import dns.resolver
from datetime import datetime

router = APIRouter(prefix="/domain", tags=["Domain & WHOIS"])

@router.get("/", summary="API Info")
def domain_info():
    return {
        "name": "Domain & WHOIS Lookup API",
        "version": "1.0.0",
        "endpoints": ["/domain/whois", "/domain/dns", "/domain/availability"],
        "powered_by": "Tools That Work"
    }

@router.get("/whois", summary="Get WHOIS information for a domain")
def whois_lookup(
    domain: str = Query(..., description="Domain name (e.g. example.com)")
):
    try:
        domain = domain.lower().strip().replace("https://", "").replace("http://", "").split("/")[0]
        w = whois.whois(domain)
        def fmt_date(d):
            if isinstance(d, list):
                d = d[0]
            if isinstance(d, datetime):
                return d.isoformat()
            return str(d) if d else None
        return {
            "domain": domain,
            "registrar": w.registrar,
            "creation_date": fmt_date(w.creation_date),
            "expiration_date": fmt_date(w.expiration_date),
            "updated_date": fmt_date(w.updated_date),
            "status": w.status if isinstance(w.status, list) else [w.status] if w.status else [],
            "name_servers": [ns.lower() for ns in (w.name_servers or [])] if w.name_servers else [],
            "registrant_country": w.country,
            "emails": w.emails if isinstance(w.emails, list) else [w.emails] if w.emails else [],
            "dnssec": w.dnssec
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"WHOIS lookup failed: {str(e)}")

@router.get("/dns", summary="Get DNS records for a domain")
def dns_lookup(
    domain: str = Query(..., description="Domain name"),
    record_type: str = Query("A", description="DNS record type: A, AAAA, MX, TXT, NS, CNAME, SOA")
):
    try:
        domain = domain.lower().strip().replace("https://", "").replace("http://", "").split("/")[0]
        answers = dns.resolver.resolve(domain, record_type.upper())
        records = []
        for rdata in answers:
            records.append(str(rdata))
        return {
            "domain": domain,
            "record_type": record_type.upper(),
            "records": records,
            "count": len(records)
        }
    except dns.resolver.NXDOMAIN:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' does not exist")
    except dns.resolver.NoAnswer:
        return {"domain": domain, "record_type": record_type.upper(), "records": [], "count": 0}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DNS lookup failed: {str(e)}")

@router.get("/availability", summary="Check if a domain is available for registration")
def check_availability(
    domain: str = Query(..., description="Domain name to check (e.g. mycooldomain.com)")
):
    try:
        domain = domain.lower().strip().replace("https://", "").replace("http://", "").split("/")[0]
        try:
            socket.gethostbyname(domain)
            resolves = True
        except socket.gaierror:
            resolves = False

        try:
            w = whois.whois(domain)
            has_whois = bool(w.domain_name)
        except Exception:
            has_whois = False

        available = not resolves and not has_whois
        return {
            "domain": domain,
            "available": available,
            "resolves": resolves,
            "has_whois_record": has_whois,
            "note": "This is a best-effort check. Always verify with your registrar before purchasing."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Availability check failed: {str(e)}")
