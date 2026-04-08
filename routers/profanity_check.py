"""
Profanity Filter & Content Moderation API
Uses better-profanity (offline)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from better_profanity import profanity

router = APIRouter(prefix="/profanity", tags=["Profanity Filter"])
profanity.load_censor_words()

class TextRequest(BaseModel):
    text: str
    censor_char: str = "*"

class BulkRequest(BaseModel):
    texts: List[str]
    censor_char: str = "*"

@router.get("/", summary="API Info")
def profanity_info():
    return {
        "name": "Profanity Filter and Content Moderation API",
        "version": "1.0.0",
        "endpoints": ["/profanity/check", "/profanity/censor", "/profanity/bulk"],
        "powered_by": "Tools That Work"
    }

@router.get("/check", summary="Check if text contains profanity")
def check_profanity(text: str = Query(..., description="Text to check")):
    contains = profanity.contains_profanity(text)
    censored = profanity.censor(text)
    words_found = []
    if contains:
        original_words = text.split()
        censored_words = censored.split()
        words_found = list(set(
            original_words[i] for i in range(min(len(original_words), len(censored_words)))
            if original_words[i] != censored_words[i]
        ))
    return {
        "text": text,
        "contains_profanity": contains,
        "profane_words_found": words_found,
        "word_count": len(text.split()),
        "is_clean": not contains,
    }

@router.get("/censor", summary="Censor profanity in text")
def censor_text(
    text: str = Query(..., description="Text to censor"),
    censor_char: str = Query("*", description="Character to replace profanity with (default: *)")
):
    if len(censor_char) != 1:
        raise HTTPException(status_code=400, detail="censor_char must be a single character")
    contains = profanity.contains_profanity(text)
    profanity.load_censor_words()
    censored = profanity.censor(text, censor_char)
    return {
        "original": text,
        "censored": censored,
        "contained_profanity": contains,
        "changed": text != censored,
    }

@router.post("/bulk", summary="Check/censor multiple texts (max 100)")
def bulk_check(req: BulkRequest):
    if len(req.texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per request")
    results = []
    for text in req.texts:
        contains = profanity.contains_profanity(text)
        results.append({
            "text": text[:100],
            "is_clean": not contains,
            "censored": profanity.censor(text, req.censor_char) if contains else text,
        })
    clean_count = sum(1 for r in results if r["is_clean"])
    return {
        "results": results,
        "total": len(results),
        "clean_count": clean_count,
        "flagged_count": len(results) - clean_count,
    }
