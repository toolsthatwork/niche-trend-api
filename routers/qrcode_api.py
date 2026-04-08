"""
QR Code Generator API
Generates QR codes as PNG, SVG, or base64
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
import qrcode
import qrcode.image.svg
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, CircleModuleDrawer
import io
import base64
from typing import Optional

router = APIRouter(prefix="/qrcode", tags=["QR Code Generator"])

@router.get("/", summary="API Info")
def qrcode_info():
    return {
        "name": "QR Code Generator API",
        "version": "1.0.0",
        "endpoints": ["/qrcode/generate", "/qrcode/generate/svg", "/qrcode/generate/base64"],
        "powered_by": "Tools That Work"
    }

@router.get("/generate", summary="Generate a QR code as PNG image")
def generate_qr(
    data: str = Query(..., description="The data to encode (URL, text, email, phone, etc.)"),
    size: int = Query(10, ge=1, le=40, description="QR code box size (1-40, default 10)"),
    border: int = Query(4, ge=0, le=10, description="Border size in boxes (default 4)"),
    fill_color: str = Query("black", description="Foreground color (e.g. 'black', '#000000')"),
    back_color: str = Query("white", description="Background color (e.g. 'white', '#ffffff')"),
    style: str = Query("square", description="Module style: square, rounded, circle")
):
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        if style == "rounded":
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                fill_color=fill_color,
                back_color=back_color
            )
        elif style == "circle":
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=CircleModuleDrawer(),
                fill_color=fill_color,
                back_color=back_color
            )
        else:
            img = qr.make_image(fill_color=fill_color, back_color=back_color)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return Response(content=buf.read(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"QR generation failed: {str(e)}")

@router.get("/generate/base64", summary="Generate QR code as base64 string")
def generate_qr_base64(
    data: str = Query(..., description="The data to encode"),
    size: int = Query(10, ge=1, le=40, description="Box size"),
    border: int = Query(4, ge=0, le=10, description="Border size"),
    fill_color: str = Query("black", description="Foreground color"),
    back_color: str = Query("white", description="Background color")
):
    try:
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=size, border=border)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return {
            "data": data,
            "format": "PNG",
            "encoding": "base64",
            "image": f"data:image/png;base64,{b64}",
            "size": f"{img.size[0]}x{img.size[1]}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"QR generation failed: {str(e)}")

@router.get("/generate/svg", summary="Generate QR code as SVG")
def generate_qr_svg(
    data: str = Query(..., description="The data to encode"),
    size: int = Query(10, ge=1, le=40, description="Box size")
):
    try:
        factory = qrcode.image.svg.SvgPathImage
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=size, border=4, image_factory=factory)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image()
        buf = io.BytesIO()
        img.save(buf)
        return Response(content=buf.getvalue(), media_type="image/svg+xml")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SVG generation failed: {str(e)}")
