"""
Text Tools API
Slugify, word count, truncate, reading time, case conversion — offline
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import re
import unicodedata

router = APIRouter(prefix="/text", tags=["Text Tools"])

def slugify(text: str, separator: str = "-") -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-_\s]+", separator, text).strip(separator)

class TextRequest(BaseModel):
    text: str

@router.get("/", summary="API Info")
def text_info():
    return {
        "name": "Text Tools API",
        "version": "1.0.0",
        "endpoints": ["/text/stats", "/text/slug", "/text/truncate", "/text/case", "/text/clean", "/text/extract"],
        "powered_by": "Tools That Work"
    }

@router.get("/stats", summary="Get word count, char count, reading time, etc.")
def text_stats(text: str = Query(..., description="Text to analyze")):
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    word_count = len(words)
    char_count = len(text)
    char_no_spaces = len(text.replace(" ", ""))
    reading_time_sec = round(word_count / 238 * 60)
    speaking_time_sec = round(word_count / 130 * 60)
    return {
        "word_count": word_count,
        "character_count": char_count,
        "character_count_no_spaces": char_no_spaces,
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "line_count": len(text.splitlines()),
        "avg_words_per_sentence": round(word_count / max(len(sentences), 1), 1),
        "avg_word_length": round(sum(len(w) for w in words) / max(word_count, 1), 1),
        "reading_time_seconds": reading_time_sec,
        "reading_time_display": f"{reading_time_sec // 60}m {reading_time_sec % 60}s",
        "speaking_time_seconds": speaking_time_sec,
        "unique_words": len(set(w.lower().strip(".,!?;:\"'") for w in words)),
    }

@router.get("/slug", summary="Convert text to URL slug")
def text_slug(
    text: str = Query(..., description="Text to slugify"),
    separator: str = Query("-", description="Separator character (- or _)"),
):
    if separator not in ("-", "_", "."):
        raise HTTPException(status_code=400, detail="Separator must be -, _, or .")
    return {"original": text, "slug": slugify(text, separator), "separator": separator}

@router.get("/truncate", summary="Truncate text to a character or word limit")
def truncate_text(
    text: str = Query(..., description="Text to truncate"),
    max_chars: int = Query(None, ge=1, description="Maximum characters"),
    max_words: int = Query(None, ge=1, description="Maximum words"),
    ellipsis: str = Query("...", description="Suffix to add when truncated"),
):
    if not max_chars and not max_words:
        raise HTTPException(status_code=400, detail="Provide max_chars or max_words")
    original_len = len(text)
    if max_words:
        words = text.split()
        if len(words) > max_words:
            text = " ".join(words[:max_words]) + ellipsis
    if max_chars and len(text) > max_chars:
        text = text[:max_chars - len(ellipsis)] + ellipsis
    return {
        "original_length": original_len,
        "truncated": text,
        "truncated_length": len(text),
        "was_truncated": len(text) < original_len or text.endswith(ellipsis),
    }

@router.get("/case", summary="Convert text case")
def convert_case(
    text: str = Query(..., description="Text to convert"),
    to: str = Query(..., description="Case type: upper, lower, title, sentence, camel, pascal, snake, kebab, constant")
):
    to = to.lower()
    words = re.sub(r"[-_\s]+", " ", text).split()
    if to == "upper": result = text.upper()
    elif to == "lower": result = text.lower()
    elif to == "title": result = text.title()
    elif to == "sentence": result = text.capitalize()
    elif to == "camel": result = words[0].lower() + "".join(w.capitalize() for w in words[1:]) if words else ""
    elif to == "pascal": result = "".join(w.capitalize() for w in words)
    elif to == "snake": result = "_".join(w.lower() for w in words)
    elif to == "kebab": result = "-".join(w.lower() for w in words)
    elif to == "constant": result = "_".join(w.upper() for w in words)
    else: raise HTTPException(status_code=400, detail="Invalid case type. Use: upper, lower, title, sentence, camel, pascal, snake, kebab, constant")
    return {"original": text, "converted": result, "case": to}

@router.get("/clean", summary="Clean and normalize text")
def clean_text(
    text: str = Query(..., description="Text to clean"),
    remove_extra_spaces: bool = Query(True),
    remove_html: bool = Query(True),
    normalize_unicode: bool = Query(True),
    strip_punctuation: bool = Query(False),
):
    if remove_html:
        text = re.sub(r"<[^>]+>", " ", text)
    if normalize_unicode:
        text = unicodedata.normalize("NFKC", text)
    if strip_punctuation:
        text = re.sub(r"[^\w\s]", "", text)
    if remove_extra_spaces:
        text = re.sub(r"\s+", " ", text).strip()
    return {"cleaned": text, "length": len(text)}

@router.get("/extract", summary="Extract emails, URLs, or numbers from text")
def extract_from_text(
    text: str = Query(..., description="Text to extract from"),
    extract: str = Query(..., description="What to extract: emails, urls, numbers, hashtags, mentions, phone_numbers")
):
    patterns = {
        "emails": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        "urls": r"https?://[^\s<>\"{}|\\^`\[\]]+",
        "numbers": r"-?\d+\.?\d*",
        "hashtags": r"#\w+",
        "mentions": r"@\w+",
        "phone_numbers": r"\+?[\d\s\-().]{7,20}",
    }
    if extract not in patterns:
        raise HTTPException(status_code=400, detail=f"Extract type must be one of: {list(patterns.keys())}")
    matches = re.findall(patterns[extract], text)
    unique = list(dict.fromkeys(matches))
    return {"extract": extract, "matches": unique, "count": len(unique)}
