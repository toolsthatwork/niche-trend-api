"""
Barcode Generator API
Uses python-barcode + Pillow (offline, free)
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import barcode
from barcode.writer import ImageWriter, SVGWriter
import io
import base64

router = APIRouter(prefix="/barcode", tags=["Barcode Generator"])

SUPPORTED_FORMATS = {
    "code128": "Code 128 (alphanumeric, most flexible)",
    "code39": "Code 39 (alphanumeric)",
    "ean13": "EAN-13 (13 digits, retail)",
    "ean8": "EAN-8 (8 digits, small retail)",
    "upca": "UPC-A (12 digits, North American retail)",
    "isbn13": "ISBN-13 (books)",
    "isbn10": "ISBN-10 (books, legacy)",
    "issn": "ISSN (periodicals)",
}

def generate_barcode(data: str, fmt: str, output_format: str) -> io.BytesIO:
    try:
        barcode_class = barcode.get_barcode_class(fmt)
        if output_format == "svg":
            writer = SVGWriter()
            buf = io.BytesIO()
            barcode_class(data, writer=writer).write(buf)
        else:
            writer = ImageWriter()
            buf = io.BytesIO()
            barcode_class(data, writer=writer).write(buf)
        buf.seek(0)
        return buf
    except barcode.errors.BarcodeNotFoundError:
        raise HTTPException(status_code=400, detail=f"Unsupported barcode format: {fmt}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Barcode generation failed: {str(e)}")

@router.get("/", summary="API Info")
def barcode_info():
    return {
        "name": "Barcode Generator API",
        "version": "1.0.0",
        "endpoints": ["/barcode/generate", "/barcode/generate/base64", "/barcode/formats"],
        "powered_by": "Tools That Work"
    }

@router.get("/generate", summary="Generate a barcode as PNG image")
def generate_png(
    data: str = Query(..., description="Data to encode in the barcode"),
    format: str = Query("code128", description="Barcode format: code128, code39, ean13, ean8, upca, isbn13, isbn10, issn")
):
    fmt = format.lower().replace("-", "")
    if fmt not in SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Supported: {list(SUPPORTED_FORMATS.keys())}")
    buf = generate_barcode(data, fmt, "png")
    return StreamingResponse(buf, media_type="image/png",
                             headers={"Content-Disposition": f"inline; filename=barcode.png"})

@router.get("/generate/svg", summary="Generate a barcode as SVG")
def generate_svg(
    data: str = Query(..., description="Data to encode"),
    format: str = Query("code128", description="Barcode format")
):
    fmt = format.lower().replace("-", "")
    if fmt not in SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {list(SUPPORTED_FORMATS.keys())}")
    buf = generate_barcode(data, fmt, "svg")
    return StreamingResponse(buf, media_type="image/svg+xml",
                             headers={"Content-Disposition": f"inline; filename=barcode.svg"})

@router.get("/generate/base64", summary="Generate a barcode as base64 PNG")
def generate_b64(
    data: str = Query(..., description="Data to encode"),
    format: str = Query("code128", description="Barcode format")
):
    fmt = format.lower().replace("-", "")
    if fmt not in SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {list(SUPPORTED_FORMATS.keys())}")
    buf = generate_barcode(data, fmt, "png")
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    return {
        "data": data,
        "format": fmt,
        "image_base64": encoded,
        "data_uri": f"data:image/png;base64,{encoded}"
    }

@router.get("/formats", summary="List supported barcode formats")
def list_formats():
    return {"formats": [{"code": k, "description": v} for k, v in SUPPORTED_FORMATS.items()]}
