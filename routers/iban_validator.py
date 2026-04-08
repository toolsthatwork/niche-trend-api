"""
IBAN Validator API
Offline validation using MOD-97 algorithm + country format rules
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
import re

router = APIRouter(prefix="/iban", tags=["IBAN Validator"])

# Country code: (length, name)
IBAN_FORMATS = {
    "AD": (24, "Andorra"), "AE": (23, "United Arab Emirates"), "AL": (28, "Albania"),
    "AT": (20, "Austria"), "AZ": (28, "Azerbaijan"), "BA": (20, "Bosnia and Herzegovina"),
    "BE": (16, "Belgium"), "BG": (22, "Bulgaria"), "BH": (22, "Bahrain"),
    "BR": (29, "Brazil"), "BY": (28, "Belarus"), "CH": (21, "Switzerland"),
    "CR": (22, "Costa Rica"), "CY": (28, "Cyprus"), "CZ": (24, "Czech Republic"),
    "DE": (22, "Germany"), "DK": (18, "Denmark"), "DO": (28, "Dominican Republic"),
    "EE": (20, "Estonia"), "EG": (29, "Egypt"), "ES": (24, "Spain"),
    "FI": (18, "Finland"), "FO": (18, "Faroe Islands"), "FR": (27, "France"),
    "GB": (22, "United Kingdom"), "GE": (22, "Georgia"), "GI": (23, "Gibraltar"),
    "GL": (18, "Greenland"), "GR": (27, "Greece"), "GT": (28, "Guatemala"),
    "HR": (21, "Croatia"), "HU": (28, "Hungary"), "IE": (22, "Ireland"),
    "IL": (23, "Israel"), "IQ": (23, "Iraq"), "IS": (26, "Iceland"),
    "IT": (27, "Italy"), "JO": (30, "Jordan"), "KW": (30, "Kuwait"),
    "KZ": (20, "Kazakhstan"), "LB": (28, "Lebanon"), "LC": (32, "Saint Lucia"),
    "LI": (21, "Liechtenstein"), "LT": (20, "Lithuania"), "LU": (20, "Luxembourg"),
    "LV": (21, "Latvia"), "LY": (25, "Libya"), "MC": (27, "Monaco"),
    "MD": (24, "Moldova"), "ME": (22, "Montenegro"), "MK": (19, "North Macedonia"),
    "MR": (27, "Mauritania"), "MT": (31, "Malta"), "MU": (30, "Mauritius"),
    "NL": (18, "Netherlands"), "NO": (15, "Norway"), "PK": (24, "Pakistan"),
    "PL": (28, "Poland"), "PS": (29, "Palestinian Territory"), "PT": (25, "Portugal"),
    "QA": (29, "Qatar"), "RO": (24, "Romania"), "RS": (22, "Serbia"),
    "SA": (24, "Saudi Arabia"), "SC": (31, "Seychelles"), "SD": (18, "Sudan"),
    "SE": (24, "Sweden"), "SI": (19, "Slovenia"), "SK": (24, "Slovakia"),
    "SM": (27, "San Marino"), "ST": (25, "São Tomé and Príncipe"), "SV": (28, "El Salvador"),
    "TL": (23, "Timor-Leste"), "TN": (24, "Tunisia"), "TR": (26, "Turkey"),
    "UA": (29, "Ukraine"), "VA": (22, "Vatican"), "VG": (24, "Virgin Islands (British)"),
    "XK": (20, "Kosovo"),
}

def validate_iban(iban: str) -> dict:
    iban_clean = re.sub(r"\s+", "", iban.upper())
    if len(iban_clean) < 4:
        return {"valid": False, "error": "IBAN too short"}

    country = iban_clean[:2]
    if not country.isalpha():
        return {"valid": False, "error": "Invalid country code"}

    if country not in IBAN_FORMATS:
        return {"valid": False, "error": f"Unknown country code: {country}"}

    expected_len = IBAN_FORMATS[country][0]
    if len(iban_clean) != expected_len:
        return {"valid": False, "error": f"Invalid length for {country}: expected {expected_len}, got {len(iban_clean)}"}

    # MOD-97 check
    rearranged = iban_clean[4:] + iban_clean[:4]
    converted = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
    if int(converted) % 97 != 1:
        return {"valid": False, "error": "Invalid IBAN checksum (MOD-97 failed)"}

    check_digits = iban_clean[2:4]
    bban = iban_clean[4:]
    formatted = " ".join(iban_clean[i:i+4] for i in range(0, len(iban_clean), 4))

    return {
        "valid": True,
        "iban": iban_clean,
        "formatted": formatted,
        "country_code": country,
        "country": IBAN_FORMATS[country][1],
        "check_digits": check_digits,
        "bban": bban,
        "length": len(iban_clean),
    }

class BulkRequest(BaseModel):
    ibans: List[str]

@router.get("/", summary="API Info")
def iban_info():
    return {
        "name": "IBAN Validator API",
        "version": "1.0.0",
        "endpoints": ["/iban/validate", "/iban/validate/bulk", "/iban/countries"],
        "powered_by": "Tools That Work"
    }

@router.get("/validate", summary="Validate an IBAN number")
def validate(iban: str = Query(..., description="IBAN to validate (spaces allowed)")):
    return validate_iban(iban)

@router.post("/validate/bulk", summary="Validate multiple IBANs (max 100)")
def validate_bulk(req: BulkRequest):
    if len(req.ibans) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 IBANs per request")
    return {"results": [validate_iban(iban) for iban in req.ibans], "count": len(req.ibans)}

@router.get("/countries", summary="List supported countries and IBAN lengths")
def list_countries():
    return {"countries": [{"code": k, "name": v[1], "iban_length": v[0]} for k, v in sorted(IBAN_FORMATS.items())], "count": len(IBAN_FORMATS)}
