"""
Unit Converter API
Length, weight, temperature, volume, area, speed, data — fully offline
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/convert", tags=["Unit Converter"])

CONVERSIONS = {
    "length": {
        "meter": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001, "mile": 1609.344,
        "yard": 0.9144, "foot": 0.3048, "inch": 0.0254, "nautical_mile": 1852.0,
        "light_year": 9.461e15, "au": 1.496e11,
    },
    "weight": {
        "kg": 1.0, "gram": 0.001, "mg": 1e-6, "pound": 0.453592, "ounce": 0.0283495,
        "ton": 1000.0, "short_ton": 907.185, "stone": 6.35029, "carat": 0.0002,
    },
    "volume": {
        "liter": 1.0, "ml": 0.001, "cubic_meter": 1000.0, "cubic_cm": 0.001,
        "gallon_us": 3.78541, "gallon_uk": 4.54609, "quart": 0.946353,
        "pint": 0.473176, "cup": 0.236588, "fluid_oz": 0.0295735,
        "tablespoon": 0.0147868, "teaspoon": 0.00492892,
    },
    "area": {
        "sqm": 1.0, "sqkm": 1e6, "sqcm": 1e-4, "sqmm": 1e-6,
        "sqmile": 2.59e6, "sqyard": 0.836127, "sqfoot": 0.092903,
        "sqinch": 6.4516e-4, "hectare": 10000.0, "acre": 4046.86,
    },
    "speed": {
        "ms": 1.0, "kmh": 0.277778, "mph": 0.44704, "knot": 0.514444,
        "fps": 0.3048, "mach": 340.29,
    },
    "data": {
        "bit": 1.0, "byte": 8.0, "kb": 8000.0, "mb": 8e6, "gb": 8e9, "tb": 8e12,
        "kib": 8192.0, "mib": 8388608.0, "gib": 8589934592.0,
    },
    "time": {
        "second": 1.0, "minute": 60.0, "hour": 3600.0, "day": 86400.0,
        "week": 604800.0, "month": 2629800.0, "year": 31557600.0,
        "millisecond": 0.001, "microsecond": 1e-6, "nanosecond": 1e-9,
    }
}

def convert_temp(value: float, from_unit: str, to_unit: str) -> float:
    # Convert to Celsius first
    if from_unit == "celsius": c = value
    elif from_unit == "fahrenheit": c = (value - 32) * 5/9
    elif from_unit == "kelvin": c = value - 273.15
    elif from_unit == "rankine": c = (value - 491.67) * 5/9
    else: raise ValueError(f"Unknown temperature unit: {from_unit}")
    # Convert Celsius to target
    if to_unit == "celsius": return round(c, 6)
    elif to_unit == "fahrenheit": return round(c * 9/5 + 32, 6)
    elif to_unit == "kelvin": return round(c + 273.15, 6)
    elif to_unit == "rankine": return round((c + 273.15) * 9/5, 6)
    else: raise ValueError(f"Unknown temperature unit: {to_unit}")

@router.get("/", summary="API Info")
def converter_info():
    return {
        "name": "Unit Converter API",
        "version": "1.0.0",
        "categories": list(CONVERSIONS.keys()) + ["temperature"],
        "endpoints": ["/convert/units", "/convert/temperature", "/convert/list"],
        "powered_by": "Tools That Work"
    }

@router.get("/units", summary="Convert between units")
def convert_units(
    value: float = Query(..., description="Value to convert"),
    from_unit: str = Query(..., description="Source unit (e.g. km, pound, liter)"),
    to_unit: str = Query(..., description="Target unit (e.g. mile, kg, gallon_us)"),
    category: Optional[str] = Query(None, description="Category hint: length, weight, volume, area, speed, data, time")
):
    from_unit = from_unit.lower().replace(" ", "_")
    to_unit = to_unit.lower().replace(" ", "_")

    # Find category if not specified
    if category:
        cats = [category.lower()]
    else:
        cats = [c for c, units in CONVERSIONS.items() if from_unit in units]
    if not cats:
        raise HTTPException(status_code=400, detail=f"Unknown unit: '{from_unit}'. Use /convert/list to see all units.")

    for cat in cats:
        units = CONVERSIONS.get(cat, {})
        if from_unit in units and to_unit in units:
            base_value = value * units[from_unit]
            result = base_value / units[to_unit]
            return {
                "value": value,
                "from": from_unit,
                "to": to_unit,
                "result": round(result, 8),
                "category": cat,
                "formula": f"{value} {from_unit} = {round(result, 6)} {to_unit}"
            }

    raise HTTPException(status_code=400, detail=f"Cannot convert '{from_unit}' to '{to_unit}'. They may be in different categories.")

@router.get("/temperature", summary="Convert temperature units")
def convert_temperature(
    value: float = Query(..., description="Temperature value"),
    from_unit: str = Query(..., description="Source unit: celsius, fahrenheit, kelvin, rankine"),
    to_unit: str = Query(..., description="Target unit: celsius, fahrenheit, kelvin, rankine")
):
    try:
        result = convert_temp(value, from_unit.lower(), to_unit.lower())
        return {"value": value, "from": from_unit, "to": to_unit, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/list", summary="List all available units by category")
def list_units():
    result = {"temperature": ["celsius", "fahrenheit", "kelvin", "rankine"]}
    for cat, units in CONVERSIONS.items():
        result[cat] = list(units.keys())
    return result
