"""
Language Detection API
Uses langdetect (offline, Google's language-detection port)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from langdetect import detect, detect_langs, LangDetectException

router = APIRouter(prefix="/language", tags=["Language Detection"])

LANGUAGE_NAMES = {
    "af": "Afrikaans", "ar": "Arabic", "bg": "Bulgarian", "bn": "Bengali",
    "ca": "Catalan", "cs": "Czech", "cy": "Welsh", "da": "Danish",
    "de": "German", "el": "Greek", "en": "English", "es": "Spanish",
    "et": "Estonian", "fa": "Persian", "fi": "Finnish", "fr": "French",
    "gu": "Gujarati", "he": "Hebrew", "hi": "Hindi", "hr": "Croatian",
    "hu": "Hungarian", "id": "Indonesian", "it": "Italian", "ja": "Japanese",
    "kn": "Kannada", "ko": "Korean", "lt": "Lithuanian", "lv": "Latvian",
    "mk": "Macedonian", "ml": "Malayalam", "mr": "Marathi", "ne": "Nepali",
    "nl": "Dutch", "no": "Norwegian", "pa": "Punjabi", "pl": "Polish",
    "pt": "Portuguese", "ro": "Romanian", "ru": "Russian", "sk": "Slovak",
    "sl": "Slovenian", "so": "Somali", "sq": "Albanian", "sv": "Swedish",
    "sw": "Swahili", "ta": "Tamil", "te": "Telugu", "th": "Thai",
    "tl": "Filipino", "tr": "Turkish", "uk": "Ukrainian", "ur": "Urdu",
    "vi": "Vietnamese", "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)"
}

class BatchDetectRequest(BaseModel):
    texts: List[str]

@router.get("/", summary="API Info")
def language_info():
    return {
        "name": "Language Detection API",
        "version": "1.0.0",
        "endpoints": ["/language/detect", "/language/detect/bulk", "/language/supported"],
        "powered_by": "Tools That Work"
    }

@router.get("/detect", summary="Detect the language of a text")
def detect_language(
    text: str = Query(..., description="Text to detect language for"),
    probabilities: bool = Query(False, description="Return language probabilities")
):
    if len(text.strip()) < 3:
        raise HTTPException(status_code=400, detail="Text too short for detection")
    try:
        if probabilities:
            langs = detect_langs(text)
            return {
                "text": text[:100],
                "detected": [
                    {
                        "code": str(l.lang),
                        "language": LANGUAGE_NAMES.get(str(l.lang), str(l.lang)),
                        "probability": round(l.prob, 4)
                    } for l in langs
                ]
            }
        else:
            code = detect(text)
            return {
                "text": text[:100],
                "code": code,
                "language": LANGUAGE_NAMES.get(code, code),
                "reliable": len(text) > 20
            }
    except LangDetectException:
        raise HTTPException(status_code=422, detail="Could not detect language — text may be too short or ambiguous")

@router.post("/detect/bulk", summary="Detect language for multiple texts (max 50)")
def detect_bulk(req: BatchDetectRequest):
    if len(req.texts) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 texts per request")
    results = []
    for text in req.texts:
        try:
            code = detect(text)
            results.append({
                "text": text[:100],
                "code": code,
                "language": LANGUAGE_NAMES.get(code, code)
            })
        except LangDetectException:
            results.append({"text": text[:100], "code": None, "language": "Unknown"})
    return {"results": results, "count": len(results)}

@router.get("/supported", summary="List all supported languages")
def supported_languages():
    return {
        "languages": [{"code": k, "name": v} for k, v in LANGUAGE_NAMES.items()],
        "count": len(LANGUAGE_NAMES)
    }
