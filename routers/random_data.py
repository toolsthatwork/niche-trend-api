"""
Random Data Generator API
Uses Faker (offline)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from faker import Faker
import secrets

router = APIRouter(prefix="/random", tags=["Random Data Generator"])

@router.get("/", summary="API Info")
def random_info():
    return {
        "name": "Random Data Generator API",
        "version": "1.0.0",
        "endpoints": ["/random/person", "/random/address", "/random/company", "/random/internet", "/random/text", "/random/number", "/random/bulk"],
        "powered_by": "Tools That Work"
    }

@router.get("/person", summary="Generate random person data")
def random_person(
    locale: str = Query("en_US", description="Locale: en_US, fr_FR, de_DE, es_ES, ja_JP, zh_CN, pt_BR, it_IT, ru_RU"),
    count: int = Query(1, ge=1, le=50)
):
    try:
        fake = Faker(locale)
    except Exception:
        fake = Faker("en_US")
    people = []
    for _ in range(count):
        people.append({
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "full_name": fake.name(),
            "gender": secrets.choice(["Male", "Female"]),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
            "username": fake.user_name(),
            "ssn": fake.ssn() if hasattr(fake, "ssn") else None,
        })
    return {"data": people if count > 1 else people[0], "count": count, "locale": locale}

@router.get("/address", summary="Generate random address")
def random_address(
    locale: str = Query("en_US"),
    count: int = Query(1, ge=1, le=50)
):
    try:
        fake = Faker(locale)
    except Exception:
        fake = Faker("en_US")
    addresses = []
    for _ in range(count):
        addresses.append({
            "street": fake.street_address(),
            "city": fake.city(),
            "state": fake.state() if hasattr(fake, "state") else None,
            "postal_code": fake.postcode(),
            "country": fake.country(),
            "country_code": fake.country_code(),
            "full_address": fake.address(),
            "latitude": float(fake.latitude()),
            "longitude": float(fake.longitude()),
        })
    return {"data": addresses if count > 1 else addresses[0], "count": count}

@router.get("/company", summary="Generate random company data")
def random_company(
    locale: str = Query("en_US"),
    count: int = Query(1, ge=1, le=20)
):
    try:
        fake = Faker(locale)
    except Exception:
        fake = Faker("en_US")
    companies = []
    for _ in range(count):
        companies.append({
            "name": fake.company(),
            "suffix": fake.company_suffix(),
            "catch_phrase": fake.catch_phrase(),
            "bs": fake.bs(),
            "email": fake.company_email(),
            "website": fake.url(),
            "phone": fake.phone_number(),
            "ein": fake.ein() if hasattr(fake, "ein") else None,
        })
    return {"data": companies if count > 1 else companies[0], "count": count}

@router.get("/internet", summary="Generate random internet/tech data")
def random_internet(count: int = Query(1, ge=1, le=50)):
    fake = Faker()
    items = []
    for _ in range(count):
        items.append({
            "email": fake.email(),
            "username": fake.user_name(),
            "password": fake.password(length=12),
            "url": fake.url(),
            "ipv4": fake.ipv4(),
            "ipv6": fake.ipv6(),
            "mac_address": fake.mac_address(),
            "user_agent": fake.user_agent(),
            "slug": fake.slug(),
        })
    return {"data": items if count > 1 else items[0], "count": count}

@router.get("/text", summary="Generate random text / lorem ipsum")
def random_text(
    sentences: int = Query(3, ge=1, le=50),
    paragraphs: int = Query(1, ge=1, le=10)
):
    fake = Faker()
    result = []
    for _ in range(paragraphs):
        result.append(" ".join(fake.sentences(nb=sentences)))
    return {
        "paragraphs": result,
        "paragraph_count": paragraphs,
        "sentence_count": sentences * paragraphs,
        "word_count": sum(len(p.split()) for p in result)
    }

@router.get("/number", summary="Generate random number with stats")
def random_number(
    min_val: int = Query(1),
    max_val: int = Query(100),
    count: int = Query(1, ge=1, le=1000)
):
    if min_val >= max_val:
        raise HTTPException(status_code=400, detail="min_val must be less than max_val")
    numbers = [secrets.randbelow(max_val - min_val + 1) + min_val for _ in range(count)]
    return {
        "numbers": numbers if count <= 100 else numbers,
        "count": count,
        "min": min(numbers),
        "max": max(numbers),
        "sum": sum(numbers),
        "average": round(sum(numbers) / len(numbers), 2)
    }

@router.get("/credit-card", summary="Generate fake credit card data (testing only)")
def random_credit_card():
    fake = Faker()
    return {
        "note": "FOR TESTING ONLY — not real card numbers",
        "number": fake.credit_card_number(),
        "provider": fake.credit_card_provider(),
        "expiry": fake.credit_card_expire(),
        "security_code": fake.credit_card_security_code(),
        "holder": fake.name(),
    }
