"""
Hash Generator API
Uses Python's built-in hashlib (offline)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import hashlib
import hmac

router = APIRouter(prefix="/hash", tags=["Hash Generator"])

ALGORITHMS = {
    "md5": "MD5 (128-bit, fast, not for passwords)",
    "sha1": "SHA-1 (160-bit, deprecated for security)",
    "sha256": "SHA-256 (256-bit, secure)",
    "sha384": "SHA-384 (384-bit, secure)",
    "sha512": "SHA-512 (512-bit, very secure)",
    "sha3_256": "SHA3-256 (256-bit, latest standard)",
    "sha3_512": "SHA3-512 (512-bit, latest standard)",
    "blake2b": "BLAKE2b (fast and secure)",
    "blake2s": "BLAKE2s (fast, 256-bit)",
}

class BulkHashRequest(BaseModel):
    texts: List[str]
    algorithm: str = "sha256"

@router.get("/", summary="API Info")
def hash_info():
    return {
        "name": "Hash Generator API",
        "version": "1.0.0",
        "endpoints": ["/hash/generate", "/hash/bulk", "/hash/verify", "/hash/algorithms"],
        "powered_by": "Tools That Work"
    }

@router.get("/generate", summary="Generate hash of a string")
def generate_hash(
    text: str = Query(..., description="Text to hash"),
    algorithm: str = Query("sha256", description="Hash algorithm: md5, sha1, sha256, sha384, sha512, sha3_256, sha3_512, blake2b, blake2s"),
    encoding: str = Query("utf-8", description="Text encoding (utf-8, ascii, latin-1)")
):
    alg = algorithm.lower().replace("-", "_")
    if alg not in ALGORITHMS:
        raise HTTPException(status_code=400, detail=f"Unsupported algorithm. Use: {list(ALGORITHMS.keys())}")
    try:
        data = text.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        raise HTTPException(status_code=400, detail=f"Invalid encoding: {encoding}")
    try:
        h = hashlib.new(alg, data)
        return {
            "input": text,
            "algorithm": alg,
            "hash": h.hexdigest(),
            "length_bits": h.digest_size * 8,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/generate/all", summary="Generate hashes using all algorithms")
def generate_all(
    text: str = Query(..., description="Text to hash")
):
    data = text.encode("utf-8")
    hashes = {}
    for alg in ALGORITHMS:
        try:
            hashes[alg] = hashlib.new(alg, data).hexdigest()
        except Exception:
            pass
    return {"input": text, "hashes": hashes}

@router.get("/verify", summary="Verify if text matches a hash")
def verify_hash(
    text: str = Query(..., description="Original text"),
    hash_value: str = Query(..., description="Hash to verify against"),
    algorithm: str = Query("sha256", description="Hash algorithm used")
):
    alg = algorithm.lower().replace("-", "_")
    if alg not in ALGORITHMS:
        raise HTTPException(status_code=400, detail=f"Unsupported algorithm: {list(ALGORITHMS.keys())}")
    try:
        computed = hashlib.new(alg, text.encode("utf-8")).hexdigest()
        match = hmac.compare_digest(computed.lower(), hash_value.lower())
        return {"match": match, "algorithm": alg, "computed": computed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk", summary="Hash multiple strings (max 100)")
def bulk_hash(req: BulkHashRequest):
    if len(req.texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts per request")
    alg = req.algorithm.lower().replace("-", "_")
    if alg not in ALGORITHMS:
        raise HTTPException(status_code=400, detail=f"Unsupported algorithm: {list(ALGORITHMS.keys())}")
    results = []
    for text in req.texts:
        h = hashlib.new(alg, text.encode("utf-8")).hexdigest()
        results.append({"input": text, "hash": h})
    return {"algorithm": alg, "results": results, "count": len(results)}

@router.get("/algorithms", summary="List supported hash algorithms")
def list_algorithms():
    return {"algorithms": [{"name": k, "description": v} for k, v in ALGORITHMS.items()]}
