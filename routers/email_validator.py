"""
Email Validation API
Validates emails with syntax, DNS MX, disposable domain, and role-based checks
"""
from fastapi import APIRouter, HTTPException, Query, Body
import re
import dns.resolver
import socket
from typing import List

router = APIRouter(prefix="/email", tags=["Email Validator"])

# Common disposable email domains
DISPOSABLE_DOMAINS = {
    "mailinator.com","guerrillamail.com","tempmail.com","throwaway.email",
    "yopmail.com","sharklasers.com","guerrillamailblock.com","grr.la",
    "guerrillamail.info","guerrillamail.biz","guerrillamail.de","guerrillamail.net",
    "guerrillamail.org","spam4.me","trashmail.com","trashmail.me","trashmail.net",
    "dispostable.com","mailnull.com","spamgourmet.com","spamgourmet.net",
    "maildrop.cc","10minutemail.com","10minutemail.net","temp-mail.org",
    "fakeinbox.com","mailnesia.com","mailnull.com","spambox.us",
    "discard.email","spamcorpse.com","getairmail.com","filzmail.com",
    "throwam.com","tempr.email","dispostable.com","mt2015.com","mt2014.com",
}

ROLE_BASED = {
    "admin","administrator","webmaster","hostmaster","postmaster","root",
    "info","support","help","contact","sales","marketing","billing",
    "noreply","no-reply","donotreply","do-not-reply","abuse","security",
    "privacy","legal","compliance","hr","careers","jobs","newsletter",
}

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')

def check_mx(domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except Exception:
        try:
            socket.gethostbyname(domain)
            return True
        except Exception:
            return False

def validate_single(email: str) -> dict:
    email = email.strip().lower()
    result = {
        "email": email,
        "valid": False,
        "syntax_valid": False,
        "domain_valid": False,
        "mx_found": False,
        "disposable": False,
        "role_based": False,
        "score": 0,
        "reason": ""
    }

    if not EMAIL_REGEX.match(email):
        result["reason"] = "Invalid email syntax"
        return result
    result["syntax_valid"] = True

    parts = email.split("@")
    local, domain = parts[0], parts[1]

    result["disposable"] = domain in DISPOSABLE_DOMAINS
    result["role_based"] = local in ROLE_BASED

    mx = check_mx(domain)
    result["mx_found"] = mx
    result["domain_valid"] = mx

    # Score
    score = 0
    if result["syntax_valid"]: score += 30
    if result["mx_found"]: score += 40
    if not result["disposable"]: score += 20
    if not result["role_based"]: score += 10
    result["score"] = score
    result["valid"] = score >= 70

    if result["disposable"]:
        result["reason"] = "Disposable email domain"
    elif not result["mx_found"]:
        result["reason"] = "Domain has no mail server (MX record not found)"
    elif result["role_based"]:
        result["reason"] = "Role-based email address"
    else:
        result["reason"] = "Valid email"

    return result

@router.get("/", summary="API Info")
def email_info():
    return {
        "name": "Email Validation API",
        "version": "1.0.0",
        "endpoints": ["/email/validate", "/email/validate/bulk"],
        "powered_by": "Tools That Work"
    }

@router.get("/validate", summary="Validate a single email address")
def validate_email(
    email: str = Query(..., description="Email address to validate")
):
    return validate_single(email)

@router.post("/validate/bulk", summary="Validate up to 100 emails at once")
def validate_bulk(
    emails: List[str] = Body(..., description="List of email addresses (max 100)")
):
    if len(emails) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 emails per request")
    results = [validate_single(e) for e in emails]
    valid_count = sum(1 for r in results if r["valid"])
    return {
        "total": len(emails),
        "valid": valid_count,
        "invalid": len(emails) - valid_count,
        "results": results
    }
