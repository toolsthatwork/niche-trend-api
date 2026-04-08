"""
Color Tools API
HEX/RGB/HSL/CMYK conversions, color names, palette generation — fully offline
"""
from fastapi import APIRouter, HTTPException, Query
import math
import re

router = APIRouter(prefix="/color", tags=["Color Tools"])

# Basic named colors
NAMED_COLORS = {
    "red": "#FF0000", "green": "#008000", "blue": "#0000FF", "white": "#FFFFFF",
    "black": "#000000", "yellow": "#FFFF00", "orange": "#FFA500", "purple": "#800080",
    "pink": "#FFC0CB", "cyan": "#00FFFF", "magenta": "#FF00FF", "lime": "#00FF00",
    "indigo": "#4B0082", "violet": "#EE82EE", "gold": "#FFD700", "silver": "#C0C0C0",
    "brown": "#A52A2A", "gray": "#808080", "grey": "#808080", "navy": "#000080",
    "teal": "#008080", "maroon": "#800000", "coral": "#FF7F50", "salmon": "#FA8072",
    "khaki": "#F0E68C", "turquoise": "#40E0D0", "lavender": "#E6E6FA",
    "beige": "#F5F5DC", "ivory": "#FFFFF0", "crimson": "#DC143C",
}

def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b) -> str:
    return "#{:02X}{:02X}{:02X}".format(r, g, b)

def rgb_to_hsl(r, g, b) -> tuple:
    r, g, b = r/255, g/255, b/255
    cmax, cmin = max(r,g,b), min(r,g,b)
    delta = cmax - cmin
    l = (cmax + cmin) / 2
    s = 0 if delta == 0 else delta / (1 - abs(2*l - 1))
    if delta == 0: h = 0
    elif cmax == r: h = 60 * (((g-b)/delta) % 6)
    elif cmax == g: h = 60 * ((b-r)/delta + 2)
    else: h = 60 * ((r-g)/delta + 4)
    return round(h, 1), round(s*100, 1), round(l*100, 1)

def rgb_to_cmyk(r, g, b) -> tuple:
    r, g, b = r/255, g/255, b/255
    k = 1 - max(r, g, b)
    if k == 1: return 0, 0, 0, 100
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return round(c*100, 1), round(m*100, 1), round(y*100, 1), round(k*100, 1)

def hsl_to_rgb(h, s, l) -> tuple:
    s, l = s/100, l/100
    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs((h/60) % 2 - 1))
    m = l - c/2
    if h < 60: r,g,b = c,x,0
    elif h < 120: r,g,b = x,c,0
    elif h < 180: r,g,b = 0,c,x
    elif h < 240: r,g,b = 0,x,c
    elif h < 300: r,g,b = x,0,c
    else: r,g,b = c,0,x
    return round((r+m)*255), round((g+m)*255), round((b+m)*255)

def luminance(r, g, b) -> float:
    def chan(c):
        c /= 255
        return c/12.92 if c <= 0.03928 else ((c+0.055)/1.055)**2.4
    return 0.2126*chan(r) + 0.7152*chan(g) + 0.0722*chan(b)

def closest_name(r, g, b) -> str:
    best, best_dist = "unknown", float("inf")
    for name, hex_val in NAMED_COLORS.items():
        nr, ng, nb = hex_to_rgb(hex_val)
        d = (r-nr)**2 + (g-ng)**2 + (b-nb)**2
        if d < best_dist:
            best_dist, best = d, name
    return best

@router.get("/", summary="API Info")
def color_info():
    return {
        "name": "Color Tools API",
        "version": "1.0.0",
        "endpoints": ["/color/convert", "/color/name", "/color/palette", "/color/contrast", "/color/random"],
        "powered_by": "Tools That Work"
    }

@router.get("/convert", summary="Convert color between HEX, RGB, HSL, CMYK")
def convert_color(
    hex: str = Query(None, description="HEX color (e.g. #FF5733 or FF5733)"),
    r: int = Query(None, ge=0, le=255, description="Red (0-255)"),
    g: int = Query(None, ge=0, le=255, description="Green (0-255)"),
    b: int = Query(None, ge=0, le=255, description="Blue (0-255)"),
    h: float = Query(None, ge=0, le=360, description="Hue (0-360)"),
    s: float = Query(None, ge=0, le=100, description="Saturation (0-100)"),
    l: float = Query(None, ge=0, le=100, description="Lightness (0-100)"),
):
    try:
        if hex:
            hex = hex.lstrip("#")
            if not re.fullmatch(r"[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}", hex):
                raise HTTPException(status_code=400, detail="Invalid HEX color")
            rv, gv, bv = hex_to_rgb(hex)
        elif r is not None and g is not None and b is not None:
            rv, gv, bv = r, g, b
        elif h is not None and s is not None and l is not None:
            rv, gv, bv = hsl_to_rgb(h, s, l)
        else:
            raise HTTPException(status_code=400, detail="Provide hex, rgb (r+g+b), or hsl (h+s+l)")
        hv, sv, lv = rgb_to_hsl(rv, gv, bv)
        cv, mv, yv, kv = rgb_to_cmyk(rv, gv, bv)
        lum = luminance(rv, gv, bv)
        return {
            "hex": rgb_to_hex(rv, gv, bv),
            "rgb": {"r": rv, "g": gv, "b": bv},
            "hsl": {"h": hv, "s": sv, "l": lv},
            "cmyk": {"c": cv, "m": mv, "y": yv, "k": kv},
            "css_rgb": f"rgb({rv}, {gv}, {bv})",
            "css_hsl": f"hsl({hv}, {sv}%, {lv}%)",
            "luminance": round(lum, 4),
            "is_dark": lum < 0.179,
            "closest_name": closest_name(rv, gv, bv),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/contrast", summary="Calculate contrast ratio between two colors")
def contrast_ratio(
    color1: str = Query(..., description="First color HEX (e.g. #FFFFFF)"),
    color2: str = Query(..., description="Second color HEX (e.g. #000000)")
):
    try:
        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)
        l1 = luminance(r1, g1, b1) + 0.05
        l2 = luminance(r2, g2, b2) + 0.05
        ratio = max(l1, l2) / min(l1, l2)
        return {
            "color1": color1.upper() if color1.startswith("#") else f"#{color1.upper()}",
            "color2": color2.upper() if color2.startswith("#") else f"#{color2.upper()}",
            "contrast_ratio": round(ratio, 2),
            "wcag_aa_normal": ratio >= 4.5,
            "wcag_aa_large": ratio >= 3.0,
            "wcag_aaa_normal": ratio >= 7.0,
            "wcag_aaa_large": ratio >= 4.5,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/random", summary="Generate random colors")
def random_color(count: int = Query(5, ge=1, le=20)):
    import secrets
    colors = []
    for _ in range(count):
        rv = secrets.randbelow(256)
        gv = secrets.randbelow(256)
        bv = secrets.randbelow(256)
        h, s, l = rgb_to_hsl(rv, gv, bv)
        colors.append({
            "hex": rgb_to_hex(rv, gv, bv),
            "rgb": {"r": rv, "g": gv, "b": bv},
            "hsl": {"h": h, "s": s, "l": l},
        })
    return {"colors": colors, "count": count}
