"""
Image Tools API
Fetch image from URL, get metadata, convert to base64 — uses Pillow + requests
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from PIL import Image, ImageOps
import requests
import io
import base64

router = APIRouter(prefix="/image", tags=["Image Tools"])

MAX_SIZE_MB = 5

def fetch_image(url: str) -> Image.Image:
    r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, stream=True)
    r.raise_for_status()
    content_type = r.headers.get("Content-Type", "")
    if "image" not in content_type:
        raise HTTPException(status_code=400, detail=f"URL does not point to an image (Content-Type: {content_type})")
    size_mb = int(r.headers.get("Content-Length", 0)) / 1e6
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"Image too large (>{MAX_SIZE_MB}MB)")
    data = b""
    for chunk in r.iter_content(chunk_size=65536):
        data += chunk
        if len(data) > MAX_SIZE_MB * 1e6:
            raise HTTPException(status_code=400, detail="Image too large")
    return Image.open(io.BytesIO(data))

@router.get("/", summary="API Info")
def image_info():
    return {
        "name": "Image Tools API",
        "version": "1.0.0",
        "endpoints": ["/image/info", "/image/base64", "/image/resize", "/image/placeholder"],
        "powered_by": "Tools That Work"
    }

@router.get("/info", summary="Get metadata from an image URL")
def image_metadata(url: str = Query(..., description="Public image URL")):
    try:
        img = fetch_image(url)
        return {
            "url": url,
            "format": img.format,
            "mode": img.mode,
            "width": img.width,
            "height": img.height,
            "aspect_ratio": round(img.width / img.height, 3),
            "orientation": "landscape" if img.width > img.height else "portrait" if img.height > img.width else "square",
            "megapixels": round(img.width * img.height / 1e6, 2),
            "has_transparency": img.mode in ("RGBA", "LA", "PA", "P"),
            "exif": {k: str(v) for k, v in (img._getexif() or {}).items()} if hasattr(img, "_getexif") and img._getexif() else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not process image: {str(e)}")

@router.get("/base64", summary="Convert image URL to base64")
def image_to_base64(
    url: str = Query(..., description="Public image URL"),
    format: str = Query("original", description="Output format: original, jpeg, png, webp")
):
    try:
        img = fetch_image(url)
        buf = io.BytesIO()
        fmt = format.upper() if format != "original" else (img.format or "PNG")
        if fmt == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format=fmt)
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        mime = f"image/{fmt.lower()}"
        return {
            "url": url,
            "format": fmt,
            "width": img.width,
            "height": img.height,
            "base64": encoded,
            "data_uri": f"data:{mime};base64,{encoded}",
            "size_bytes": len(encoded) * 3 // 4,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/placeholder", summary="Generate a placeholder image")
def placeholder(
    width: int = Query(400, ge=1, le=2000),
    height: int = Query(300, ge=1, le=2000),
    bg_color: str = Query("CCCCCC", description="Background color hex (without #)"),
    text_color: str = Query("666666", description="Text color hex (without #)"),
    text: str = Query(None, description="Custom label (default: WxH)"),
    format: str = Query("png", description="Output format: png or jpeg")
):
    try:
        bg = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))
        fg = tuple(int(text_color[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid color hex. Use 6-digit hex without #.")
    img = Image.new("RGB", (width, height), bg)
    label = text or f"{width}x{height}"
    try:
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        # Draw text in center
        bbox = draw.textbbox((0, 0), label)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((width - tw) // 2, (height - th) // 2), label, fill=fg)
    except Exception:
        pass
    buf = io.BytesIO()
    img.save(buf, format=format.upper())
    buf.seek(0)
    return StreamingResponse(buf, media_type=f"image/{format.lower()}")
