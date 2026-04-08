"""
Phone Number Validation API
Uses Google's libphonenumber (free, offline, no API key)
"""
from fastapi import APIRouter, HTTPException, Query
import phonenumbers
from phonenumbers import geocoder, carrier, timezone

router = APIRouter(prefix="/phone", tags=["Phone Validator"])

@router.get("/", summary="API Info")
def phone_info():
    return {
        "name": "Phone Number Validation API",
        "version": "1.0.0",
        "endpoints": ["/phone/validate", "/phone/format"],
        "powered_by": "Tools That Work"
    }

@router.get("/validate", summary="Validate and look up a phone number")
def validate_phone(
    number: str = Query(..., description="Phone number (include country code, e.g. +14155552671)"),
    country: str = Query(None, description="Default country code if number lacks +prefix (e.g. US, CA, GB)")
):
    try:
        parsed = phonenumbers.parse(number, country)
        is_valid = phonenumbers.is_valid_number(parsed)
        is_possible = phonenumbers.is_possible_number(parsed)
        number_type = phonenumbers.number_type(parsed)
        type_map = {
            0: "FIXED_LINE", 1: "MOBILE", 2: "FIXED_LINE_OR_MOBILE",
            3: "TOLL_FREE", 4: "PREMIUM_RATE", 5: "SHARED_COST",
            6: "VOIP", 7: "PERSONAL_NUMBER", 8: "PAGER", 9: "UAN",
            10: "VOICEMAIL", 27: "UNKNOWN"
        }
        location = geocoder.description_for_number(parsed, "en")
        carrier_name = carrier.name_for_number(parsed, "en")
        timezones = list(timezone.time_zones_for_number(parsed))
        return {
            "input": number,
            "valid": is_valid,
            "possible": is_possible,
            "country_code": f"+{parsed.country_code}",
            "national_number": str(parsed.national_number),
            "e164_format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
            "international_format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "national_format": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "number_type": type_map.get(number_type, "UNKNOWN"),
            "location": location or None,
            "carrier": carrier_name or None,
            "timezones": timezones
        }
    except phonenumbers.phonenumberutil.NumberParseException as e:
        raise HTTPException(status_code=400, detail=f"Invalid phone number: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Phone validation failed: {str(e)}")

@router.get("/format", summary="Format a phone number in multiple formats")
def format_phone(
    number: str = Query(..., description="Phone number with country code"),
    country: str = Query(None, description="Default country if no + prefix")
):
    try:
        parsed = phonenumbers.parse(number, country)
        return {
            "input": number,
            "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
            "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "rfc3966": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.RFC3966),
            "valid": phonenumbers.is_valid_number(parsed)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
