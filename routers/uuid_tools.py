"""
UUID / GUID Generator API
Python built-in uuid module — fully offline
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
import uuid
import re

router = APIRouter(prefix="/uuid", tags=["UUID Generator"])

def validate_uuid(value: str) -> dict:
    value = value.strip().lower()
    pattern = re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-([1-5])[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", value)
    if not pattern:
        return {"uuid": value, "valid": False, "error": "Invalid UUID format"}
    version = int(pattern.group(1))
    try:
        parsed = uuid.UUID(value)
        return {
            "uuid": str(parsed),
            "valid": True,
            "version": version,
            "variant": str(parsed.variant),
            "urn": parsed.urn,
            "hex": parsed.hex,
            "int": parsed.int,
        }
    except Exception as e:
        return {"uuid": value, "valid": False, "error": str(e)}

class BulkValidateRequest(BaseModel):
    uuids: List[str]

@router.get("/", summary="API Info")
def uuid_info():
    return {
        "name": "UUID and GUID Generator API",
        "version": "1.0.0",
        "endpoints": ["/uuid/v1", "/uuid/v4", "/uuid/v5", "/uuid/bulk", "/uuid/validate", "/uuid/nil"],
        "powered_by": "Tools That Work"
    }

@router.get("/v4", summary="Generate UUID v4 (random)")
def generate_v4(count: int = Query(1, ge=1, le=100, description="Number of UUIDs to generate (1-100)")):
    ids = [str(uuid.uuid4()) for _ in range(count)]
    return {
        "uuids": ids if count > 1 else ids[0],
        "count": count,
        "version": 4,
        "format": "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx",
    }

@router.get("/v1", summary="Generate UUID v1 (time-based)")
def generate_v1(count: int = Query(1, ge=1, le=100)):
    ids = [str(uuid.uuid1()) for _ in range(count)]
    return {
        "uuids": ids if count > 1 else ids[0],
        "count": count,
        "version": 1,
        "note": "v1 UUIDs encode the current timestamp and MAC address",
    }

@router.get("/v5", summary="Generate UUID v5 (name-based, SHA-1)")
def generate_v5(
    name: str = Query(..., description="Name to hash into UUID"),
    namespace: str = Query("dns", description="Namespace: dns, url, oid, x500, or a custom UUID")
):
    namespaces = {
        "dns": uuid.NAMESPACE_DNS,
        "url": uuid.NAMESPACE_URL,
        "oid": uuid.NAMESPACE_OID,
        "x500": uuid.NAMESPACE_X500,
    }
    if namespace in namespaces:
        ns = namespaces[namespace]
    else:
        try:
            ns = uuid.UUID(namespace)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid namespace. Use: dns, url, oid, x500, or a valid UUID")
    result = uuid.uuid5(ns, name)
    return {
        "uuid": str(result),
        "name": name,
        "namespace": namespace,
        "version": 5,
        "deterministic": True,
        "note": "Same name + namespace always produces the same UUID",
    }

@router.get("/bulk", summary="Generate multiple UUIDs v4 (up to 1000)")
def bulk_generate(
    count: int = Query(10, ge=1, le=1000),
    format: str = Query("standard", description="Output format: standard (with dashes), hex (no dashes), urn")
):
    ids = []
    for _ in range(count):
        u = uuid.uuid4()
        if format == "hex":
            ids.append(u.hex)
        elif format == "urn":
            ids.append(u.urn)
        else:
            ids.append(str(u))
    return {"uuids": ids, "count": count, "format": format, "version": 4}

@router.get("/validate", summary="Validate a UUID and get its details")
def validate(value: str = Query(..., description="UUID to validate")):
    return validate_uuid(value)

@router.post("/validate/bulk", summary="Validate multiple UUIDs (max 100)")
def validate_bulk(req: BulkValidateRequest):
    if len(req.uuids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 UUIDs per request")
    results = [validate_uuid(u) for u in req.uuids]
    valid_count = sum(1 for r in results if r.get("valid"))
    return {"results": results, "total": len(results), "valid": valid_count, "invalid": len(results) - valid_count}

@router.get("/nil", summary="Get the nil UUID (all zeros)")
def nil_uuid():
    return {
        "uuid": "00000000-0000-0000-0000-000000000000",
        "description": "The nil UUID — all bits set to zero. Used as a null/empty UUID value.",
        "hex": "0" * 32,
        "int": 0,
    }
