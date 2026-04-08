#!/usr/bin/env python3
"""
RapidAPI listing automation via Playwright.
Opens a real browser, lets you log in, then auto-creates all API listings.

Install deps first:
    pip install playwright
    playwright install chromium

Run:
    python automate_rapidapi.py
"""

import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

SPECS_DIR = Path(__file__).parent / "specs"

APIS = [
    {"file": "currency.json",           "name": "Currency and Forex Exchange"},
    {"file": "qrcode.json",             "name": "QR Code Generator"},
    {"file": "email_validator.json",    "name": "Email Validator and Verifier"},
    {"file": "weather.json",            "name": "Weather and Forecast"},
    {"file": "ip_geolocation.json",     "name": "IP Geolocation"},
    {"file": "phone_validator.json",    "name": "Phone Number Validator"},
    {"file": "sentiment_analysis.json", "name": "Sentiment and Text Analysis"},
    {"file": "domain_whois.json",       "name": "Domain and WHOIS Lookup"},
    {"file": "crypto_prices.json",      "name": "Crypto and Token Prices"},
    {"file": "stock_prices.json",       "name": "Stock Prices and Market Data"},
    {"file": "language_detection.json", "name": "Language Detection"},
    {"file": "text_translation.json",   "name": "Text Translation"},
    {"file": "word_dictionary.json",    "name": "Word Dictionary and Definitions"},
    {"file": "barcode_generator.json",  "name": "Barcode Generator"},
    {"file": "country_information.json","name": "Country Information"},
    {"file": "timezone.json",           "name": "Timezone API"},
    {"file": "password_tools.json",     "name": "Password Generator and Strength Checker"},
    {"file": "hash_generator.json",     "name": "Hash Generator"},
    {"file": "url_tools.json",          "name": "URL Tools and Redirect Tracer"},
    {"file": "color_tools.json",        "name": "Color Converter and Tools"},
    {"file": "base64_tools.json",       "name": "Base64 Encode and Decode"},
    {"file": "unit_converter.json",     "name": "Unit Converter"},
    {"file": "postal_code.json",        "name": "Postal Code Lookup"},
    {"file": "book_lookup.json",        "name": "Book and ISBN Lookup"},
    {"file": "readability.json",        "name": "Text Readability Score"},
    {"file": "holidays.json",           "name": "Public Holidays"},
    {"file": "mortgage_calculator.json","name": "Mortgage and Loan Calculator"},
    {"file": "health_calculator.json",  "name": "Health and Fitness Calculator"},
    {"file": "random_data.json",        "name": "Random Data Generator"},
    {"file": "age_calculator.json",     "name": "Age Calculator"},
    {"file": "number_to_words.json",    "name": "Number to Words Converter"},
    {"file": "text_tools.json",         "name": "Text Tools and Utilities"},
    {"file": "regex_tools.json",        "name": "Regex Tester and Tools"},
    {"file": "image_tools.json",        "name": "Image Tools and Utilities"},
    {"file": "carbon_footprint.json",   "name": "Carbon Footprint Calculator"},
    {"file": "iban_validator.json",     "name": "IBAN Validator"},
    {"file": "profanity_filter.json",   "name": "Profanity Filter and Content Moderation"},
    {"file": "ssl_checker.json",        "name": "SSL Certificate Checker"},
    {"file": "uuid_generator.json",     "name": "UUID and GUID Generator"},
]

PRICING_TIERS = [
    {"name": "BASIC",  "price": 0,     "requests": 100,     "description": "Free tier"},
    {"name": "PRO",    "price": 9.99,  "requests": 1000,    "description": "Pro tier"},
    {"name": "ULTRA",  "price": 29.99, "requests": 10000,   "description": "Ultra tier"},
    {"name": "MEGA",   "price": 79.99, "requests": 100000,  "description": "Mega tier"},
]


async def wait_for_login(page):
    print("\n[!] Browser is open. Please log in to RapidAPI as 'toolsthatwork'.")
    print("    When you're logged in and see your dashboard, press ENTER here.")
    input("    --> Press ENTER to continue: ")
    print("[OK] Continuing...\n")


async def create_api_listing(page, api_info):
    name = api_info["name"]
    spec_path = SPECS_DIR / api_info["file"]

    print(f"\n[...] Creating: {name}")

    # Navigate to provider hub
    await page.goto("https://rapidapi.com/provider", wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)

    # Click "Add New API" button
    try:
        add_btn = page.get_by_role("button", name="Add New API")
        await add_btn.wait_for(timeout=10000)
        await add_btn.click()
    except PWTimeout:
        # Try alternative selectors
        await page.click('text=Add New API')
    await page.wait_for_timeout(1500)

    # Click OpenAPI tab
    try:
        openapi_tab = page.get_by_role("tab", name="OpenAPI")
        await openapi_tab.click()
    except Exception:
        await page.click('text=OpenAPI')
    await page.wait_for_timeout(1000)

    # Upload the spec file
    async with page.expect_file_chooser() as fc_info:
        try:
            upload_btn = page.get_by_role("button", name="Upload File")
            await upload_btn.click()
        except Exception:
            await page.click('text=Upload File')
    file_chooser = await fc_info.value
    await file_chooser.set_files(str(spec_path))
    await page.wait_for_timeout(3000)

    # Click Next/Create/Save — varies by RapidAPI version
    for btn_text in ["Create API", "Next", "Save", "Import"]:
        try:
            btn = page.get_by_role("button", name=btn_text)
            if await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(2000)
                break
        except Exception:
            continue

    print(f"    [OK] Uploaded spec for: {name}")
    print(f"         Now set pricing manually if needed, or run pricing automation separately.")
    return True


async def main():
    print("=" * 60)
    print("  RapidAPI Listing Automation — Tools That Work")
    print("=" * 60)
    print(f"  APIs to create: {len(APIS)}")
    print(f"  Specs directory: {SPECS_DIR}")
    print()

    # Verify all spec files exist
    missing = [a["file"] for a in APIS if not (SPECS_DIR / a["file"]).exists()]
    if missing:
        print(f"[ERROR] Missing spec files: {missing}")
        return

    print("[OK] All spec files found.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context()
        page = await context.new_page()

        # Open RapidAPI login
        await page.goto("https://rapidapi.com/auth/sign-in", wait_until="domcontentloaded")

        await wait_for_login(page)

        success = []
        failed = []

        for api in APIS:
            try:
                ok = await create_api_listing(page, api)
                if ok:
                    success.append(api["name"])
            except Exception as e:
                print(f"    [FAIL] {api['name']}: {e}")
                failed.append(api["name"])
                # Pause and let user fix it manually before continuing
                input(f"    Fix it in the browser if needed, then press ENTER to continue...")

        print("\n" + "=" * 60)
        print(f"  Done! {len(success)}/{len(APIS)} APIs created successfully.")
        if success:
            print("\n  Created:")
            for s in success:
                print(f"    [OK] {s}")
        if failed:
            print("\n  Failed (create manually):")
            for f in failed:
                print(f"    [X]  {f}")
        print("=" * 60)

        input("\nPress ENTER to close the browser...")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
