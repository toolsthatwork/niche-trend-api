#!/usr/bin/env python3
"""
Generate individual OpenAPI spec files for each API router.
Run: python generate_openapi_specs.py
Output: specs/ directory with one JSON file per API
"""
import json
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_URL = "https://niche-trend-api.onrender.com"
OUT_DIR = Path("specs")
OUT_DIR.mkdir(exist_ok=True)

APIS = [
    {
        "name": "currency",
        "title": "Currency and Forex Exchange",
        "description": "Real-time and historical currency exchange rates for 30+ currencies. Powered by European Central Bank data via Frankfurter. No API key setup required on your end.",
        "prefix": "/currency",
        "module": "routers.currency",
        "router_attr": "router",
    },
    {
        "name": "qrcode",
        "title": "QR Code Generator",
        "description": "Generate QR codes as PNG, SVG, or base64. Supports custom colors, rounded and circle styles, adjustable size and border. Perfect for URLs, vCards, WiFi codes, and more.",
        "prefix": "/qrcode",
        "module": "routers.qrcode_api",
        "router_attr": "router",
    },
    {
        "name": "email_validator",
        "title": "Email Validator and Verifier",
        "description": "Validate email addresses with syntax checking, DNS MX record verification, disposable domain detection, and role-based email flagging. Supports bulk validation of up to 100 emails per request.",
        "prefix": "/email",
        "module": "routers.email_validator",
        "router_attr": "router",
    },
    {
        "name": "weather",
        "title": "Weather and Forecast",
        "description": "Current weather, 16-day forecasts, and coordinate-based lookups for any city worldwide. Powered by Open-Meteo using ECMWF data. Includes temperature, humidity, wind, precipitation, and condition codes.",
        "prefix": "/weather",
        "module": "routers.weather",
        "router_attr": "router",
    },
    {
        "name": "ip_geolocation",
        "title": "IP Geolocation",
        "description": "Look up geolocation data for any IPv4 or IPv6 address. Returns country, region, city, coordinates, timezone, ISP, and proxy/VPN/hosting detection. Supports bulk lookups of up to 50 IPs.",
        "prefix": "/ip",
        "module": "routers.ip_geo",
        "router_attr": "router",
    },
    {
        "name": "phone_validator",
        "title": "Phone Number Validator",
        "description": "Validate and format phone numbers from 240+ countries. Returns E164, international, and national formats, number type (mobile, landline, VOIP), carrier, location, and timezone. Powered by Google libphonenumber.",
        "prefix": "/phone",
        "module": "routers.phone_validator",
        "router_attr": "router",
    },
    {
        "name": "sentiment_analysis",
        "title": "Sentiment and Text Analysis",
        "description": "Analyze sentiment (positive, negative, neutral), subjectivity, tone, and extract keywords from any text. Supports single and batch analysis of up to 50 texts per request.",
        "prefix": "/sentiment",
        "module": "routers.sentiment",
        "router_attr": "router",
    },
    {
        "name": "domain_whois",
        "title": "Domain and WHOIS Lookup",
        "description": "Look up WHOIS registration data, DNS records (A, MX, TXT, NS, CNAME), and domain availability. Works for any registered domain worldwide.",
        "prefix": "/domain",
        "module": "routers.domain_lookup",
        "router_attr": "router",
    },
    {
        "name": "crypto_prices",
        "title": "Crypto and Token Prices",
        "description": "Get real-time prices, market caps, and 24h changes for 10000+ cryptocurrencies. Includes trending coins, top coins by market cap, historical price charts, and multi-currency conversion. Powered by CoinGecko.",
        "prefix": "/crypto",
        "module": "routers.crypto",
        "router_attr": "router",
    },
    {
        "name": "stock_prices",
        "title": "Stock Prices and Market Data",
        "description": "Real-time stock quotes, historical price data, and company fundamentals for any publicly traded company. Get price, market cap, P/E ratio, 52-week high/low, and multi-symbol quotes. Powered by Yahoo Finance.",
        "prefix": "/stocks",
        "module": "routers.stocks",
        "router_attr": "router",
    },
    {
        "name": "language_detection",
        "title": "Language Detection",
        "description": "Detect the language of any text with confidence scores. Supports 55+ languages including English, French, Spanish, Chinese, Arabic, Japanese, and more. Bulk detection of up to 50 texts per request.",
        "prefix": "/language",
        "module": "routers.language_detection",
        "router_attr": "router",
    },
    {
        "name": "text_translation",
        "title": "Text Translation",
        "description": "Translate text between 70+ languages. Supports auto language detection, bulk translation of up to 10 texts, and returns both translated text and language metadata.",
        "prefix": "/translate",
        "module": "routers.translate",
        "router_attr": "router",
    },
    {
        "name": "word_dictionary",
        "title": "Word Dictionary and Definitions",
        "description": "Get definitions, phonetics, synonyms, antonyms, and usage examples for any English word. Returns multiple meanings grouped by part of speech (noun, verb, adjective, etc.).",
        "prefix": "/dictionary",
        "module": "routers.dictionary",
        "router_attr": "router",
    },
    {
        "name": "barcode_generator",
        "title": "Barcode Generator",
        "description": "Generate barcodes as PNG, SVG, or base64. Supports Code 128, Code 39, EAN-13, EAN-8, UPC-A, ISBN-13, ISBN-10, and ISSN formats. Perfect for product labels, inventory systems, and publishing.",
        "prefix": "/barcode",
        "module": "routers.barcode",
        "router_attr": "router",
    },
    {
        "name": "country_information",
        "title": "Country Information",
        "description": "Get detailed information about any country: capital, population, area, languages, currencies, timezones, calling codes, flag emoji, borders, and more. Look up by name, ISO code, or region.",
        "prefix": "/country",
        "module": "routers.country_info",
        "router_attr": "router",
    },
    {
        "name": "timezone",
        "title": "Timezone API",
        "description": "Get current time in any timezone, convert times between timezones, and list all available timezones. Supports all IANA timezone identifiers (e.g. America/New_York, Europe/Paris, Asia/Tokyo).",
        "prefix": "/timezone",
        "module": "routers.timezone_api",
        "router_attr": "router",
    },
    {
        "name": "password_tools",
        "title": "Password Generator and Strength Checker",
        "description": "Generate cryptographically secure random passwords and check password strength. Customizable length, character sets, and complexity. Returns entropy bits, strength score, and improvement suggestions.",
        "prefix": "/password",
        "module": "routers.password_tools",
        "router_attr": "router",
    },
    {
        "name": "hash_generator",
        "title": "Hash Generator",
        "description": "Generate and verify cryptographic hashes using MD5, SHA-1, SHA-256, SHA-512, SHA3-256, SHA3-512, BLAKE2b, and BLAKE2s. Supports bulk hashing of up to 100 strings per request.",
        "prefix": "/hash",
        "module": "routers.hash_tools",
        "router_attr": "router",
    },
    {
        "name": "url_tools",
        "title": "URL Tools and Redirect Tracer",
        "description": "Trace URL redirects and unshorten URLs, check HTTP status codes, parse URL components, and bulk-check up to 20 URLs. Identify redirect chains, final destinations, and server response times.",
        "prefix": "/url",
        "module": "routers.url_tools",
        "router_attr": "router",
    },
    {
        "name": "color_tools",
        "title": "Color Converter and Tools",
        "description": "Convert colors between HEX, RGB, HSL, and CMYK formats. Calculate WCAG contrast ratios for accessibility checks, generate random colors, and get the closest named color.",
        "prefix": "/color",
        "module": "routers.color_tools",
        "router_attr": "router",
    },
    {
        "name": "base64_tools",
        "title": "Base64 Encode and Decode",
        "description": "Encode text to Base64 and decode Base64 to text. Supports standard and URL-safe Base64, multiple input encodings, and validation. Handles large payloads via POST endpoints.",
        "prefix": "/base64",
        "module": "routers.base64_tools",
        "router_attr": "router",
    },
    {
        "name": "unit_converter",
        "title": "Unit Converter",
        "description": "Convert between units of length, weight, volume, area, speed, data, time, and temperature. Supports 80+ units including metric, imperial, and scientific. Fully offline with instant results.",
        "prefix": "/convert",
        "module": "routers.unit_converter",
        "router_attr": "router",
    },
    {
        "name": "postal_code",
        "title": "Postal Code Lookup",
        "description": "Look up location data (city, state, coordinates) from a postal or ZIP code, or find all postal codes for a given city and state. Supports US, Canada, UK, Germany, France, and 60+ countries.",
        "prefix": "/postal",
        "module": "routers.postal_code",
        "router_attr": "router",
    },
    {
        "name": "book_lookup",
        "title": "Book and ISBN Lookup",
        "description": "Look up books by ISBN-10 or ISBN-13. Get title, authors, publisher, publish date, page count, subjects, and cover image. Also supports full-text book search by title, author, or keyword.",
        "prefix": "/book",
        "module": "routers.book_lookup",
        "router_attr": "router",
    },
    {
        "name": "readability",
        "title": "Text Readability Score",
        "description": "Analyze text readability using Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog, SMOG, ARI, and Coleman-Liau Index. Returns reading level, estimated reading time, and difficulty classification.",
        "prefix": "/readability",
        "module": "routers.readability",
        "router_attr": "router",
    },
    {
        "name": "holidays",
        "title": "Public Holidays API",
        "description": "Get public holidays for 46+ countries by year. Check if today is a holiday, find upcoming holidays, and list holidays with dates, names, and weekdays. Supports country-specific regional holidays.",
        "prefix": "/holidays",
        "module": "routers.holidays_api",
        "router_attr": "router",
    },
    {
        "name": "mortgage_calculator",
        "title": "Mortgage and Loan Calculator",
        "description": "Calculate monthly mortgage payments, full amortization schedules, and home affordability. Supports down payments, various term lengths, and interest rates. Returns total interest paid and payment breakdowns.",
        "prefix": "/mortgage",
        "module": "routers.mortgage_calc",
        "router_attr": "router",
    },
    {
        "name": "health_calculator",
        "title": "Health and Fitness Calculator",
        "description": "Calculate BMI, BMR (Mifflin-St Jeor and Harris-Benedict), TDEE with activity multipliers, and ideal body weight. Returns calorie goals for weight loss, maintenance, and gain.",
        "prefix": "/health",
        "module": "routers.health_calc",
        "router_attr": "router",
    },
    {
        "name": "random_data",
        "title": "Random Data Generator",
        "description": "Generate realistic fake data for testing and development: persons (name, email, phone, DOB), addresses, companies, internet data (IPs, MAC, user agents), lorem ipsum text, and random numbers. Supports 10+ locales.",
        "prefix": "/random",
        "module": "routers.random_data",
        "router_attr": "router",
    },
    {
        "name": "age_calculator",
        "title": "Age Calculator",
        "description": "Calculate exact age from a date of birth, time between two dates, and days until next birthday. Returns age in years, months, days, hours, and minutes, plus zodiac sign, Chinese zodiac, and generation.",
        "prefix": "/age",
        "module": "routers.age_calc",
        "router_attr": "router",
    },
    {
        "name": "number_to_words",
        "title": "Number to Words Converter",
        "description": "Convert numbers to words in 30+ languages. Supports cardinal (forty-two), ordinal (forty-second), and currency (forty-two dollars) formats. Bulk conversion of up to 50 numbers per request.",
        "prefix": "/number2words",
        "module": "routers.number_words",
        "router_attr": "router",
    },
    {
        "name": "text_tools",
        "title": "Text Tools and Utilities",
        "description": "Comprehensive text utilities: word count, reading time, slug generation, text truncation, case conversion (camelCase, snake_case, kebab-case, etc.), text cleaning, and extraction of emails, URLs, and numbers.",
        "prefix": "/text",
        "module": "routers.text_tools",
        "router_attr": "router",
    },
    {
        "name": "regex_tools",
        "title": "Regex Tester and Tools",
        "description": "Test regular expressions against text, find all matches with positions, replace patterns, split text, and validate regex syntax. Includes a library of 12 common regex patterns for emails, URLs, phones, and more.",
        "prefix": "/regex",
        "module": "routers.regex_tools",
        "router_attr": "router",
    },
    {
        "name": "image_tools",
        "title": "Image Tools and Utilities",
        "description": "Get image metadata (dimensions, format, EXIF), convert images to base64 from a URL, and generate placeholder images of any size with custom colors and labels. Supports PNG, JPEG, and WebP.",
        "prefix": "/image",
        "module": "routers.image_tools",
        "router_attr": "router",
    },
    {
        "name": "carbon_footprint",
        "title": "Carbon Footprint Calculator",
        "description": "Calculate CO2 emissions for flights, driving, electricity, diet, and food consumption. Uses IEA and IPCC emission factors. Returns kg CO2e, tonnes, trees needed to offset, and comparisons.",
        "prefix": "/carbon",
        "module": "routers.carbon_calc",
        "router_attr": "router",
    },
    {
        "name": "iban_validator",
        "title": "IBAN Validator",
        "description": "Validate International Bank Account Numbers (IBAN) using the MOD-97 algorithm. Supports 77 countries. Returns country, check digits, BBAN, formatted IBAN, and validation error details. Bulk validation up to 100 IBANs.",
        "prefix": "/iban",
        "module": "routers.iban_validator",
        "router_attr": "router",
    },
    {
        "name": "profanity_filter",
        "title": "Profanity Filter and Content Moderation",
        "description": "Detect and censor profanity in text. Returns whether text is clean, which words were flagged, and a censored version. Supports bulk moderation of up to 100 texts per request with custom censor characters.",
        "prefix": "/profanity",
        "module": "routers.profanity_check",
        "router_attr": "router",
    },
    {
        "name": "uuid_generator",
        "title": "UUID and GUID Generator",
        "description": "Generate version 1, 4, and 5 UUIDs. Bulk generate up to 1000 v4 UUIDs per request in standard, hex, or URN format. Validate UUIDs and extract version, variant, and hex representation. Deterministic v5 UUIDs from name+namespace.",
        "prefix": "/uuid",
        "module": "routers.uuid_tools",
        "router_attr": "router",
    },
    {
        "name": "ssl_checker",
        "title": "SSL Certificate Checker",
        "description": "Check SSL certificate validity, expiry date, issuer, subject alternative names, and WCAG compliance for any domain. Bulk-check up to 20 domains at once. Returns days until expiry and expiration warnings.",
        "prefix": "/ssl",
        "module": "routers.ssl_checker",
        "router_attr": "router",
    },
]

for api in APIS:
    import importlib
    mod = importlib.import_module(api["module"])
    router = getattr(mod, api["router_attr"])

    app = FastAPI(
        title=api["title"],
        description=api["description"],
        version="1.0.0",
    )
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(router)

    spec = app.openapi()
    spec["servers"] = [{"url": BASE_URL, "description": "Production"}]

    out_path = OUT_DIR / f"{api['name']}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)
    print(f"  [OK] {out_path}")

print(f"\nGenerated {len(APIS)} OpenAPI specs in {OUT_DIR}/")
print("\nRun automate_rapidapi.py to upload all specs to RapidAPI automatically.")
