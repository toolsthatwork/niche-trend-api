"""
Password Generator & Strength Checker API
Fully offline using Python's secrets module
"""
from fastapi import APIRouter, HTTPException, Query
import secrets
import string
import re
import math

router = APIRouter(prefix="/password", tags=["Password Tools"])

COMMON_PASSWORDS = {
    "password", "123456", "password1", "12345678", "qwerty", "abc123",
    "monkey", "master", "dragon", "iloveyou", "letmein", "sunshine",
    "princess", "welcome", "shadow", "superman", "michael", "football",
    "000000", "654321", "123456789", "1234567890", "password123",
}

def calc_entropy(password: str) -> float:
    charset = 0
    if re.search(r'[a-z]', password): charset += 26
    if re.search(r'[A-Z]', password): charset += 26
    if re.search(r'\d', password): charset += 10
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password): charset += 32
    if charset == 0: return 0
    return round(len(password) * math.log2(charset), 2)

def score_password(password: str) -> dict:
    score = 0
    issues = []
    suggestions = []

    if password.lower() in COMMON_PASSWORDS:
        return {"score": 0, "strength": "Very Weak", "issues": ["This is one of the most common passwords"], "suggestions": ["Use a completely different password"]}

    if len(password) >= 8: score += 1
    else: issues.append("Too short (minimum 8 characters)"); suggestions.append("Use at least 8 characters")

    if len(password) >= 12: score += 1
    if len(password) >= 16: score += 1

    if re.search(r'[a-z]', password): score += 1
    else: issues.append("No lowercase letters"); suggestions.append("Add lowercase letters")

    if re.search(r'[A-Z]', password): score += 1
    else: issues.append("No uppercase letters"); suggestions.append("Add uppercase letters")

    if re.search(r'\d', password): score += 1
    else: issues.append("No numbers"); suggestions.append("Add numbers")

    if re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password): score += 1
    else: issues.append("No special characters"); suggestions.append("Add special characters (!@#$%...)")

    if re.search(r'(.)\1{2,}', password): score -= 1; issues.append("Repeated characters")
    if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', password.lower()): score -= 1; issues.append("Sequential characters")

    score = max(0, min(score, 7))
    strengths = {0: "Very Weak", 1: "Very Weak", 2: "Weak", 3: "Weak", 4: "Fair", 5: "Strong", 6: "Strong", 7: "Very Strong"}
    return {"score": score, "strength": strengths[score], "issues": issues, "suggestions": suggestions}

@router.get("/", summary="API Info")
def password_info():
    return {
        "name": "Password Tools API",
        "version": "1.0.0",
        "endpoints": ["/password/generate", "/password/strength", "/password/bulk"],
        "powered_by": "Tools That Work"
    }

@router.get("/generate", summary="Generate a secure random password")
def generate_password(
    length: int = Query(16, ge=8, le=128, description="Password length (8-128)"),
    uppercase: bool = Query(True, description="Include uppercase letters"),
    lowercase: bool = Query(True, description="Include lowercase letters"),
    digits: bool = Query(True, description="Include digits"),
    symbols: bool = Query(True, description="Include symbols"),
    exclude_ambiguous: bool = Query(False, description="Exclude ambiguous chars (0, O, l, 1, I)")
):
    charset = ""
    if lowercase: charset += string.ascii_lowercase
    if uppercase: charset += string.ascii_uppercase
    if digits: charset += string.digits
    if symbols: charset += "!@#$%^&*()-_=+[]{}|;:,.<>?"
    if not charset:
        raise HTTPException(status_code=400, detail="At least one character type must be selected")
    if exclude_ambiguous:
        charset = "".join(c for c in charset if c not in "0Ol1I")

    # Ensure at least one of each required type
    password = []
    if lowercase: password.append(secrets.choice(string.ascii_lowercase))
    if uppercase: password.append(secrets.choice(string.ascii_uppercase))
    if digits: password.append(secrets.choice(string.digits))
    if symbols: password.append(secrets.choice("!@#$%^&*()-_=+[]{}|;:,.<>?"))

    while len(password) < length:
        password.append(secrets.choice(charset))

    secrets.SystemRandom().shuffle(password)
    pwd = "".join(password)

    return {
        "password": pwd,
        "length": len(pwd),
        "entropy_bits": calc_entropy(pwd),
        "strength": score_password(pwd)["strength"]
    }

@router.get("/strength", summary="Check password strength")
def check_strength(
    password: str = Query(..., description="Password to evaluate")
):
    result = score_password(password)
    return {
        "password": "*" * len(password),
        "length": len(password),
        "entropy_bits": calc_entropy(password),
        **result
    }

@router.get("/bulk", summary="Generate multiple passwords")
def generate_bulk(
    count: int = Query(10, ge=1, le=50, description="Number of passwords"),
    length: int = Query(16, ge=8, le=128, description="Password length")
):
    passwords = []
    charset = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    for _ in range(count):
        pwd = "".join(secrets.choice(charset) for _ in range(length))
        passwords.append(pwd)
    return {"passwords": passwords, "count": count, "length": length}
