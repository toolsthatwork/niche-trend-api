"""
Base64 Tools API
Encode/decode text, URLs, files — Python built-in (offline)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import base64
import re

router = APIRouter(prefix="/base64", tags=["Base64 Tools"])

class EncodeRequest(BaseModel):
    text: str
    url_safe: bool = False

class DecodeRequest(BaseModel):
    encoded: str
    url_safe: bool = False

@router.get("/", summary="API Info")
def base64_info():
    return {
        "name": "Base64 Tools API",
        "version": "1.0.0",
        "endpoints": ["/base64/encode", "/base64/decode", "/base64/validate", "/base64/encode/url"],
        "powered_by": "Tools That Work"
    }

@router.get("/encode", summary="Encode text to Base64")
def encode_text(
    text: str = Query(..., description="Text to encode"),
    url_safe: bool = Query(False, description="Use URL-safe Base64 (replaces +/ with -_)"),
    encoding: str = Query("utf-8", description="Input encoding (utf-8, ascii, latin-1)")
):
    try:
        data = text.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        raise HTTPException(status_code=400, detail=f"Invalid encoding: {encoding}")
    encoded = base64.urlsafe_b64encode(data).decode("ascii") if url_safe else base64.b64encode(data).decode("ascii")
    return {
        "original": text,
        "encoded": encoded,
        "url_safe": url_safe,
        "original_length": len(text),
        "encoded_length": len(encoded),
        "padding": encoded.count("="),
    }

@router.get("/decode", summary="Decode Base64 to text")
def decode_text(
    encoded: str = Query(..., description="Base64 string to decode"),
    url_safe: bool = Query(False, description="Use URL-safe decoder"),
    encoding: str = Query("utf-8", description="Output encoding (utf-8, ascii, latin-1)")
):
    # Auto-add padding if needed
    padded = encoded + "=" * (4 - len(encoded) % 4) if len(encoded) % 4 else encoded
    try:
        if url_safe:
            data = base64.urlsafe_b64decode(padded)
        else:
            data = base64.b64decode(padded)
        text = data.decode(encoding)
        return {
            "encoded": encoded,
            "decoded": text,
            "encoding": encoding,
            "decoded_length": len(text),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decode failed: {str(e)}")

@router.get("/validate", summary="Check if a string is valid Base64")
def validate_base64(
    value: str = Query(..., description="String to validate")
):
    std_pattern = re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", value)
    url_pattern = re.fullmatch(r"[A-Za-z0-9\-_]*={0,2}", value)
    is_standard = bool(std_pattern) and len(value) % 4 == 0
    is_url_safe = bool(url_pattern) and len(value) % 4 == 0

    # Try decoding
    decoded_ok = False
    try:
        padded = value + "=" * (4 - len(value) % 4) if len(value) % 4 else value
        base64.b64decode(padded)
        decoded_ok = True
    except Exception:
        pass

    return {
        "value": value[:100],
        "is_valid": decoded_ok,
        "is_standard_base64": is_standard,
        "is_url_safe_base64": is_url_safe,
        "length": len(value),
        "has_padding": "=" in value,
    }

@router.post("/encode", summary="Encode text to Base64 (POST for long text)")
def encode_post(req: EncodeRequest):
    if len(req.text) > 100000:
        raise HTTPException(status_code=400, detail="Text exceeds 100KB limit")
    data = req.text.encode("utf-8")
    encoded = base64.urlsafe_b64encode(data).decode("ascii") if req.url_safe else base64.b64encode(data).decode("ascii")
    return {
        "encoded": encoded,
        "url_safe": req.url_safe,
        "original_bytes": len(data),
        "encoded_length": len(encoded),
    }

@router.post("/decode", summary="Decode Base64 to text (POST for long strings)")
def decode_post(req: DecodeRequest):
    padded = req.encoded + "=" * (4 - len(req.encoded) % 4) if len(req.encoded) % 4 else req.encoded
    try:
        data = base64.urlsafe_b64decode(padded) if req.url_safe else base64.b64decode(padded)
        return {"decoded": data.decode("utf-8"), "original_length": len(req.encoded)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decode failed: {str(e)}")
