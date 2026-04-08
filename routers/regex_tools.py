"""
Regex Tester API
Test regex patterns against text — Python built-in re module (offline)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import re

router = APIRouter(prefix="/regex", tags=["Regex Tools"])

FLAGS_MAP = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL, "x": re.VERBOSE}

def parse_flags(flags_str: str) -> int:
    flags = 0
    for f in flags_str.lower():
        if f in FLAGS_MAP:
            flags |= FLAGS_MAP[f]
    return flags

class TestRequest(BaseModel):
    pattern: str
    text: str
    flags: str = ""

@router.get("/", summary="API Info")
def regex_info():
    return {
        "name": "Regex Tester API",
        "version": "1.0.0",
        "endpoints": ["/regex/test", "/regex/match", "/regex/replace", "/regex/split", "/regex/validate"],
        "powered_by": "Tools That Work"
    }

@router.get("/test", summary="Test a regex pattern against text")
def test_regex(
    pattern: str = Query(..., description="Regular expression pattern"),
    text: str = Query(..., description="Text to test against"),
    flags: str = Query("", description="Flags: i=ignorecase, m=multiline, s=dotall"),
    max_matches: int = Query(100, ge=1, le=500)
):
    try:
        compiled = re.compile(pattern, parse_flags(flags))
    except re.error as e:
        raise HTTPException(status_code=400, detail=f"Invalid regex pattern: {str(e)}")

    matches = []
    for m in compiled.finditer(text):
        matches.append({
            "match": m.group(0),
            "start": m.start(),
            "end": m.end(),
            "groups": list(m.groups()),
            "named_groups": m.groupdict() if m.groupdict() else None,
        })
        if len(matches) >= max_matches:
            break

    return {
        "pattern": pattern,
        "flags": flags,
        "text_length": len(text),
        "is_match": bool(matches),
        "match_count": len(matches),
        "matches": matches,
        "truncated": len(matches) >= max_matches,
    }

@router.get("/replace", summary="Replace pattern matches in text")
def replace_regex(
    pattern: str = Query(..., description="Regex pattern to find"),
    text: str = Query(..., description="Text to process"),
    replacement: str = Query(..., description="Replacement string (use \\1 for group references)"),
    flags: str = Query(""),
    count: int = Query(0, ge=0, description="Max replacements (0 = all)")
):
    try:
        compiled = re.compile(pattern, parse_flags(flags))
        result = compiled.sub(replacement, text, count=count)
        match_count = len(compiled.findall(text))
        return {
            "original": text,
            "result": result,
            "pattern": pattern,
            "replacement": replacement,
            "replacements_made": min(match_count, count) if count else match_count,
        }
    except re.error as e:
        raise HTTPException(status_code=400, detail=f"Invalid regex: {str(e)}")

@router.get("/split", summary="Split text by regex pattern")
def split_regex(
    pattern: str = Query(..., description="Regex delimiter pattern"),
    text: str = Query(..., description="Text to split"),
    flags: str = Query(""),
    max_split: int = Query(0, ge=0, description="Max splits (0 = all)")
):
    try:
        compiled = re.compile(pattern, parse_flags(flags))
        parts = compiled.split(text, maxsplit=max_split)
        return {"parts": parts, "count": len(parts), "pattern": pattern}
    except re.error as e:
        raise HTTPException(status_code=400, detail=f"Invalid regex: {str(e)}")

@router.get("/validate", summary="Validate if a regex pattern is valid")
def validate_regex(
    pattern: str = Query(..., description="Regex pattern to validate"),
    flags: str = Query("")
):
    try:
        compiled = re.compile(pattern, parse_flags(flags))
        return {
            "pattern": pattern,
            "valid": True,
            "groups": compiled.groups,
            "group_names": list(compiled.groupindex.keys()),
        }
    except re.error as e:
        return {"pattern": pattern, "valid": False, "error": str(e)}

@router.get("/common", summary="List common regex patterns")
def common_patterns():
    return {
        "patterns": [
            {"name": "Email", "pattern": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"},
            {"name": "URL", "pattern": r"https?://[^\s<>\"{}|\\^`\[\]]+"},
            {"name": "IPv4", "pattern": r"\b(?:\d{1,3}\.){3}\d{1,3}\b"},
            {"name": "Phone (US)", "pattern": r"\+?1?\s?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}"},
            {"name": "Date (YYYY-MM-DD)", "pattern": r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])"},
            {"name": "Time (HH:MM)", "pattern": r"(?:[01]\d|2[0-3]):[0-5]\d"},
            {"name": "Hex Color", "pattern": r"#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})\b"},
            {"name": "Postal Code (US)", "pattern": r"\b\d{5}(?:-\d{4})?\b"},
            {"name": "Credit Card", "pattern": r"\b(?:\d{4}[ -]?){3}\d{4}\b"},
            {"name": "SSN", "pattern": r"\b\d{3}-\d{2}-\d{4}\b"},
            {"name": "Username", "pattern": r"^[a-zA-Z0-9_]{3,20}$"},
            {"name": "Strong Password", "pattern": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"},
        ]
    }
