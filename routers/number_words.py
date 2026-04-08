"""
Number to Words API
Uses num2words (offline, 20+ languages)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from num2words import num2words, CONVERTER_CLASSES

router = APIRouter(prefix="/number2words", tags=["Number to Words"])

SUPPORTED_LANGS = {
    "en": "English", "fr": "French", "de": "German", "es": "Spanish",
    "pt": "Portuguese", "it": "Italian", "ru": "Russian", "uk": "Ukrainian",
    "pl": "Polish", "cs": "Czech", "sk": "Slovak", "hu": "Hungarian",
    "nl": "Dutch", "sv": "Swedish", "da": "Danish", "no": "Norwegian",
    "fi": "Finnish", "tr": "Turkish", "ro": "Romanian", "ar": "Arabic",
    "he": "Hebrew", "ja": "Japanese", "ko": "Korean", "th": "Thai",
    "id": "Indonesian", "sl": "Slovenian", "sr": "Serbian", "hr": "Croatian",
    "lt": "Lithuanian", "lv": "Latvian", "et": "Estonian",
}

class BulkRequest(BaseModel):
    numbers: List[float]
    lang: str = "en"
    to: str = "cardinal"

@router.get("/", summary="API Info")
def n2w_info():
    return {
        "name": "Number to Words API",
        "version": "1.0.0",
        "endpoints": ["/number2words/convert", "/number2words/ordinal", "/number2words/currency", "/number2words/bulk"],
        "powered_by": "Tools That Work"
    }

@router.get("/convert", summary="Convert number to words")
def convert(
    number: float = Query(..., description="Number to convert (e.g. 42, 1000000, 3.14)"),
    lang: str = Query("en", description="Language code (e.g. en, fr, de, es, ru)"),
    to: str = Query("cardinal", description="Type: cardinal (forty-two), ordinal (forty-second), year, currency")
):
    lang = lang.lower()
    if lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=400, detail=f"Unsupported language. Use /number2words/languages")
    try:
        result = num2words(number, lang=lang, to=to)
        return {
            "number": number,
            "words": result,
            "lang": lang,
            "language": SUPPORTED_LANGS[lang],
            "type": to,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")

@router.get("/ordinal", summary="Convert number to ordinal words (1st, 2nd, ...)")
def ordinal(
    number: int = Query(..., description="Integer to convert to ordinal"),
    lang: str = Query("en")
):
    lang = lang.lower()
    if lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=400, detail="Unsupported language")
    try:
        return {"number": number, "ordinal": num2words(number, lang=lang, to="ordinal"),
                "ordinal_num": num2words(number, lang=lang, to="ordinal_num")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/currency", summary="Convert number to currency words")
def currency_words(
    amount: float = Query(..., description="Amount to convert"),
    lang: str = Query("en"),
    currency: str = Query("USD", description="Currency code hint (informational only)")
):
    lang = lang.lower()
    if lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=400, detail="Unsupported language")
    try:
        result = num2words(amount, lang=lang, to="currency")
        return {"amount": amount, "words": result, "currency": currency, "lang": lang}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk", summary="Convert multiple numbers (max 50)")
def bulk_convert(req: BulkRequest):
    if len(req.numbers) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 numbers per request")
    lang = req.lang.lower()
    if lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=400, detail="Unsupported language")
    results = []
    for n in req.numbers:
        try:
            results.append({"number": n, "words": num2words(n, lang=lang, to=req.to)})
        except Exception as e:
            results.append({"number": n, "words": None, "error": str(e)})
    return {"results": results, "lang": lang, "type": req.to}

@router.get("/languages", summary="List supported languages")
def languages():
    return {"languages": [{"code": k, "name": v} for k, v in SUPPORTED_LANGS.items()]}
