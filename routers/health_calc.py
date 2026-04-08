"""
Health & Fitness Calculator API
BMI, BMR, TDEE, ideal weight, body fat — fully offline
"""
from fastapi import APIRouter, HTTPException, Query
import math

router = APIRouter(prefix="/health", tags=["Health Calculator"])

@router.get("/", summary="API Info")
def health_info():
    return {
        "name": "Health and Fitness Calculator API",
        "version": "1.0.0",
        "endpoints": ["/health/bmi", "/health/bmr", "/health/tdee", "/health/ideal-weight", "/health/body-fat", "/health/calories"],
        "powered_by": "Tools That Work"
    }

@router.get("/bmi", summary="Calculate Body Mass Index (BMI)")
def bmi(
    weight_kg: float = Query(None, gt=0, description="Weight in kilograms"),
    height_cm: float = Query(None, gt=0, description="Height in centimeters"),
    weight_lb: float = Query(None, gt=0, description="Weight in pounds (alternative to kg)"),
    height_in: float = Query(None, gt=0, description="Height in inches (alternative to cm)"),
):
    if weight_lb and height_in:
        weight_kg = weight_lb * 0.453592
        height_cm = height_in * 2.54
    if not weight_kg or not height_cm:
        raise HTTPException(status_code=400, detail="Provide weight_kg + height_cm OR weight_lb + height_in")
    h_m = height_cm / 100
    bmi_val = weight_kg / (h_m ** 2)
    if bmi_val < 18.5: cat = "Underweight"
    elif bmi_val < 25: cat = "Normal weight"
    elif bmi_val < 30: cat = "Overweight"
    elif bmi_val < 35: cat = "Obese (Class I)"
    elif bmi_val < 40: cat = "Obese (Class II)"
    else: cat = "Obese (Class III)"
    normal_low = 18.5 * h_m ** 2
    normal_high = 24.9 * h_m ** 2
    return {
        "bmi": round(bmi_val, 1),
        "category": cat,
        "weight_kg": round(weight_kg, 1),
        "height_cm": round(height_cm, 1),
        "healthy_weight_range_kg": {"min": round(normal_low, 1), "max": round(normal_high, 1)},
    }

@router.get("/bmr", summary="Calculate Basal Metabolic Rate (BMR)")
def bmr(
    weight_kg: float = Query(..., gt=0),
    height_cm: float = Query(..., gt=0),
    age: int = Query(..., ge=1, le=120),
    gender: str = Query(..., description="male or female"),
    formula: str = Query("mifflin", description="Formula: mifflin (default), harris, katch")
):
    gender = gender.lower()
    if gender not in ("male", "female"):
        raise HTTPException(status_code=400, detail="gender must be 'male' or 'female'")
    if formula == "mifflin":
        base = 10 * weight_kg + 6.25 * height_cm - 5 * age
        result = base + 5 if gender == "male" else base - 161
    elif formula == "harris":
        if gender == "male":
            result = 88.362 + 13.397 * weight_kg + 4.799 * height_cm - 5.677 * age
        else:
            result = 447.593 + 9.247 * weight_kg + 3.098 * height_cm - 4.330 * age
    else:
        raise HTTPException(status_code=400, detail="Formula must be 'mifflin' or 'harris'")
    return {"bmr_calories": round(result), "formula": formula, "gender": gender,
            "weight_kg": weight_kg, "height_cm": height_cm, "age": age}

@router.get("/tdee", summary="Calculate Total Daily Energy Expenditure (TDEE)")
def tdee(
    weight_kg: float = Query(..., gt=0),
    height_cm: float = Query(..., gt=0),
    age: int = Query(..., ge=1, le=120),
    gender: str = Query(..., description="male or female"),
    activity: str = Query(..., description="sedentary, light, moderate, active, very_active, extra_active")
):
    gender = gender.lower()
    if gender not in ("male", "female"):
        raise HTTPException(status_code=400, detail="gender must be 'male' or 'female'")
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    bmr_val = base + 5 if gender == "male" else base - 161
    multipliers = {
        "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
        "active": 1.725, "very_active": 1.9, "extra_active": 2.0
    }
    if activity not in multipliers:
        raise HTTPException(status_code=400, detail=f"activity must be one of: {list(multipliers.keys())}")
    tdee_val = bmr_val * multipliers[activity]
    return {
        "tdee_calories": round(tdee_val),
        "bmr_calories": round(bmr_val),
        "activity_level": activity,
        "multiplier": multipliers[activity],
        "goals": {
            "weight_loss": round(tdee_val - 500),
            "mild_weight_loss": round(tdee_val - 250),
            "maintenance": round(tdee_val),
            "mild_weight_gain": round(tdee_val + 250),
            "weight_gain": round(tdee_val + 500),
        }
    }

@router.get("/ideal-weight", summary="Calculate ideal body weight")
def ideal_weight(
    height_cm: float = Query(..., gt=0),
    gender: str = Query(..., description="male or female"),
    frame: str = Query("medium", description="body frame: small, medium, large")
):
    gender = gender.lower()
    if gender not in ("male", "female"):
        raise HTTPException(status_code=400, detail="gender must be 'male' or 'female'")
    h_in = height_cm / 2.54
    # Hamwi formula
    if gender == "male":
        base = 48.0 + 2.7 * max(h_in - 60, 0)
    else:
        base = 45.5 + 2.2 * max(h_in - 60, 0)
    adj = {"small": -0.1, "medium": 0, "large": 0.1}
    ideal = base * (1 + adj.get(frame, 0))
    return {
        "ideal_weight_kg": round(ideal, 1),
        "ideal_weight_lb": round(ideal * 2.205, 1),
        "range_kg": {"min": round(ideal * 0.9, 1), "max": round(ideal * 1.1, 1)},
        "gender": gender,
        "height_cm": height_cm,
        "frame": frame,
        "formula": "Hamwi"
    }
