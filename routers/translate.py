"""
Text Translation API
Uses MyMemory (free, no key needed, 5000 chars/day)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import requests

router = APIRouter(prefix="/translate", tags=["Text Translation"])

BASE = "https://api.mymemory.translated.net/get"

LANGUAGES = {
    "af": "Afrikaans", "sq": "Albanian", "ar": "Arabic", "hy": "Armenian",
    "az": "Azerbaijani", "eu": "Basque", "be": "Belarusian", "bn": "Bengali",
    "bs": "Bosnian", "bg": "Bulgarian", "ca": "Catalan", "zh": "Chinese",
    "hr": "Croatian", "cs": "Czech", "da": "Danish", "nl": "Dutch",
    "en": "English", "eo": "Esperanto", "et": "Estonian", "fi": "Finnish",
    "fr": "French", "gl": "Galician", "ka": "Georgian", "de": "German",
    "el": "Greek", "gu": "Gujarati", "ht": "Haitian Creole", "he": "Hebrew",
    "hi": "Hindi", "hu": "Hungarian", "is": "Icelandic", "id": "Indonesian",
    "ga": "Irish", "it": "Italian", "ja": "Japanese", "kn": "Kannada",
    "kk": "Kazakh", "ko": "Korean", "lv": "Latvian", "lt": "Lithuanian",
    "mk": "Macedonian", "ms": "Malay", "mt": "Maltese", "mr": "Marathi",
    "mn": "Mongolian", "no": "Norwegian", "fa": "Persian", "pl": "Polish",
    "pt": "Portuguese", "ro": "Romanian", "ru": "Russian", "sr": "Serbian",
    "sk": "Slovak", "sl": "Slovenian", "es": "Spanish", "sw": "Swahili",
    "sv": "Swedish", "tl": "Filipino", "ta": "Tamil", "te": "Telugu",
    "th": "Thai", "tr": "Turkish", "uk": "Ukrainian", "ur": "Urdu",
    "vi": "Vietnamese", "cy": "Welsh", "yi": "Yiddish"
}

class BulkTranslateRequest(BaseModel):
    texts: List[str]
    source: str = "en"
    target: str

@router.get("/", summary="API Info")
def translate_info():
    return {
        "name": "Text Translation API",
        "version": "1.0.0",
        "endpoints": ["/translate/text", "/translate/bulk", "/translate/languages"],
        "powered_by": "Tools That Work"
    }

@router.get("/text", summary="Translate text between languages")
def translate_text(
    text: str = Query(..., description="Text to translate (max 500 chars)"),
    target: str = Query(..., description="Target language code (e.g. fr, es, de, ja)"),
    source: str = Query("en", description="Source language code (default: en, use 'auto' to detect)")
):
    if len(text) > 500:
        raise HTTPException(status_code=400, detail="Text exceeds 500 character limit")
    if target not in LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {target}")
    try:
        lang_pair = f"{source}|{target}"
        r = requests.get(BASE, params={"q": text, "langpair": lang_pair}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("responseStatus") != 200:
            raise HTTPException(status_code=503, detail=data.get("responseDetails", "Translation failed"))
        return {
            "original": text,
            "translated": data["responseData"]["translatedText"],
            "source": source,
            "target": target,
            "target_language": LANGUAGES.get(target, target),
            "match": data["responseData"].get("match")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Translation unavailable: {str(e)}")

@router.post("/bulk", summary="Translate multiple texts (max 10)")
def translate_bulk(req: BulkTranslateRequest):
    if len(req.texts) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 texts per request")
    if req.target not in LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {req.target}")
    results = []
    for text in req.texts:
        try:
            r = requests.get(BASE, params={
                "q": text[:500], "langpair": f"{req.source}|{req.target}"
            }, timeout=10)
            data = r.json()
            results.append({
                "original": text,
                "translated": data["responseData"]["translatedText"] if data.get("responseStatus") == 200 else None,
                "error": None if data.get("responseStatus") == 200 else data.get("responseDetails")
            })
        except Exception as e:
            results.append({"original": text, "translated": None, "error": str(e)})
    return {"results": results, "source": req.source, "target": req.target,
            "target_language": LANGUAGES.get(req.target, req.target)}

@router.get("/languages", summary="List all supported languages")
def list_languages():
    return {
        "languages": [{"code": k, "name": v} for k, v in LANGUAGES.items()],
        "count": len(LANGUAGES)
    }
