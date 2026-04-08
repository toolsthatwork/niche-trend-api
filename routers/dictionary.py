"""
Word Dictionary API
Uses dictionaryapi.dev (free, no key needed)
"""
from fastapi import APIRouter, HTTPException, Query
import requests

router = APIRouter(prefix="/dictionary", tags=["Word Dictionary"])

BASE = "https://api.dictionaryapi.dev/api/v2/entries/en"

@router.get("/", summary="API Info")
def dictionary_info():
    return {
        "name": "Word Dictionary API",
        "version": "1.0.0",
        "endpoints": ["/dictionary/define", "/dictionary/synonyms"],
        "powered_by": "Tools That Work"
    }

@router.get("/define", summary="Get definitions, synonyms, antonyms for a word")
def define_word(
    word: str = Query(..., description="Word to look up"),
    language: str = Query("en", description="Language code (currently supports: en)")
):
    word = word.strip().lower()
    if not word or len(word) > 50:
        raise HTTPException(status_code=400, detail="Invalid word")
    try:
        r = requests.get(f"{BASE}/{word}", timeout=10)
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"No definition found for '{word}'")
        r.raise_for_status()
        data = r.json()
        result = {
            "word": word,
            "phonetic": None,
            "audio": None,
            "meanings": []
        }
        # Extract phonetic and audio
        for entry in data:
            if not result["phonetic"] and entry.get("phonetic"):
                result["phonetic"] = entry["phonetic"]
            for phonetics in entry.get("phonetics", []):
                if not result["audio"] and phonetics.get("audio"):
                    result["audio"] = phonetics["audio"]
            for meaning in entry.get("meanings", []):
                m = {
                    "part_of_speech": meaning.get("partOfSpeech"),
                    "definitions": [],
                    "synonyms": meaning.get("synonyms", [])[:10],
                    "antonyms": meaning.get("antonyms", [])[:10],
                }
                for d in meaning.get("definitions", [])[:5]:
                    m["definitions"].append({
                        "definition": d.get("definition"),
                        "example": d.get("example"),
                        "synonyms": d.get("synonyms", [])[:5],
                        "antonyms": d.get("antonyms", [])[:5],
                    })
                result["meanings"].append(m)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Dictionary unavailable: {str(e)}")
