"""
Age Calculator API
Fully offline using Python datetime
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime

router = APIRouter(prefix="/age", tags=["Age Calculator"])

ZODIAC = [
    ((3, 21), (4, 19), "Aries"), ((4, 20), (5, 20), "Taurus"),
    ((5, 21), (6, 20), "Gemini"), ((6, 21), (7, 22), "Cancer"),
    ((7, 23), (8, 22), "Leo"), ((8, 23), (9, 22), "Virgo"),
    ((9, 23), (10, 22), "Libra"), ((10, 23), (11, 21), "Scorpio"),
    ((11, 22), (12, 21), "Sagittarius"), ((12, 22), (12, 31), "Capricorn"),
    ((1, 1), (1, 19), "Capricorn"), ((1, 20), (2, 18), "Aquarius"),
    ((2, 19), (3, 20), "Pisces"),
]

CHINESE_ZODIAC = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
                   "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]

def get_zodiac(month: int, day: int) -> str:
    for start, end, sign in ZODIAC:
        if (month, day) >= start and (month, day) <= end:
            return sign
    return "Unknown"

def get_chinese_zodiac(year: int) -> str:
    return CHINESE_ZODIAC[(year - 1900) % 12]

@router.get("/", summary="API Info")
def age_info():
    return {
        "name": "Age Calculator API",
        "version": "1.0.0",
        "endpoints": ["/age/calculate", "/age/between", "/age/next-birthday"],
        "powered_by": "Tools That Work"
    }

@router.get("/calculate", summary="Calculate age from date of birth")
def calculate_age(
    birthdate: str = Query(..., description="Date of birth in YYYY-MM-DD format"),
    reference_date: str = Query(None, description="Reference date (default: today) in YYYY-MM-DD format")
):
    try:
        dob = date.fromisoformat(birthdate)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid birthdate. Use YYYY-MM-DD format.")
    today = date.today() if not reference_date else date.fromisoformat(reference_date)
    if dob > today:
        raise HTTPException(status_code=400, detail="Birthdate cannot be in the future")

    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    months_total = (today.year - dob.year) * 12 + (today.month - dob.month)
    if today.day < dob.day:
        months_total -= 1
    days_total = (today - dob).days

    next_bday = dob.replace(year=today.year)
    if next_bday < today:
        next_bday = next_bday.replace(year=today.year + 1)
    days_until_birthday = (next_bday - today).days

    return {
        "birthdate": str(dob),
        "reference_date": str(today),
        "age_years": years,
        "age_months": months_total,
        "age_days": days_total,
        "age_hours": days_total * 24,
        "age_minutes": days_total * 24 * 60,
        "next_birthday": str(next_bday),
        "days_until_birthday": days_until_birthday,
        "is_birthday_today": days_until_birthday == 0 or days_until_birthday == 365,
        "zodiac_sign": get_zodiac(dob.month, dob.day),
        "chinese_zodiac": get_chinese_zodiac(dob.year),
        "birth_weekday": dob.strftime("%A"),
        "generation": (
            "Gen Alpha" if dob.year >= 2013 else
            "Gen Z" if dob.year >= 1997 else
            "Millennial" if dob.year >= 1981 else
            "Gen X" if dob.year >= 1965 else
            "Baby Boomer" if dob.year >= 1946 else
            "Silent Generation"
        )
    }

@router.get("/between", summary="Calculate time between two dates")
def between_dates(
    date1: str = Query(..., description="First date YYYY-MM-DD"),
    date2: str = Query(..., description="Second date YYYY-MM-DD")
):
    try:
        d1 = date.fromisoformat(date1)
        d2 = date.fromisoformat(date2)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    if d1 > d2:
        d1, d2 = d2, d1
    delta = d2 - d1
    years = d2.year - d1.year - ((d2.month, d2.day) < (d1.month, d1.day))
    months = (d2.year - d1.year) * 12 + (d2.month - d1.month)
    if d2.day < d1.day:
        months -= 1
    return {
        "from": str(d1), "to": str(d2),
        "years": years, "months": months,
        "weeks": delta.days // 7,
        "days": delta.days,
        "hours": delta.days * 24,
    }
