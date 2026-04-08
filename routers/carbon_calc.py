"""
Carbon Footprint Calculator API
Offline formulas based on widely-used emission factors (IEA, IPCC, EPA)
"""
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/carbon", tags=["Carbon Footprint"])

# kg CO2e per unit
EMISSION_FACTORS = {
    "electricity": {
        "us": 0.386, "eu": 0.233, "uk": 0.193, "canada": 0.130,
        "australia": 0.656, "global_average": 0.475,
    },
    "flights": {
        "economy_short": 0.255,  # kg CO2e per km per passenger
        "economy_long": 0.195,
        "business": 0.430,
        "first_class": 0.510,
    },
    "driving": {
        "gasoline_small": 0.142,   # kg CO2e per km
        "gasoline_medium": 0.192,
        "gasoline_large": 0.241,
        "diesel": 0.171,
        "hybrid": 0.105,
        "electric_us": 0.079,
        "electric_eu": 0.048,
        "motorcycle": 0.113,
    },
    "diet": {
        "vegan": 1.5,          # kg CO2e per day
        "vegetarian": 1.7,
        "pescatarian": 2.3,
        "average": 3.3,
        "high_meat": 5.6,
    },
    "natural_gas": 2.204,      # kg CO2e per cubic meter
    "beef_kg": 27.0,           # kg CO2e per kg of beef
    "chicken_kg": 6.9,
    "pork_kg": 12.1,
    "cheese_kg": 13.5,
    "milk_liter": 3.2,
    "streaming_hour": 0.036,   # kg CO2e per hour
    "email_simple": 0.0004,    # kg CO2e per email
    "email_attachment": 0.05,
}

@router.get("/", summary="API Info")
def carbon_info():
    return {
        "name": "Carbon Footprint Calculator API",
        "version": "1.0.0",
        "endpoints": ["/carbon/flight", "/carbon/driving", "/carbon/electricity", "/carbon/diet", "/carbon/lifestyle"],
        "powered_by": "Tools That Work"
    }

@router.get("/flight", summary="Calculate CO2 from a flight")
def flight_carbon(
    distance_km: float = Query(..., gt=0, description="Flight distance in kilometers"),
    passengers: int = Query(1, ge=1, le=500, description="Number of passengers"),
    cabin_class: str = Query("economy_long", description="economy_short, economy_long, business, first_class"),
    round_trip: bool = Query(False, description="Is this a round trip?")
):
    if cabin_class not in EMISSION_FACTORS["flights"]:
        raise HTTPException(status_code=400, detail=f"cabin_class must be: {list(EMISSION_FACTORS['flights'].keys())}")
    factor = EMISSION_FACTORS["flights"][cabin_class]
    multiplier = 2 if round_trip else 1
    total_km = distance_km * multiplier
    co2_per_passenger = total_km * factor
    co2_total = co2_per_passenger * passengers
    return {
        "distance_km": distance_km,
        "round_trip": round_trip,
        "total_km": total_km,
        "cabin_class": cabin_class,
        "passengers": passengers,
        "co2_per_passenger_kg": round(co2_per_passenger, 2),
        "co2_total_kg": round(co2_total, 2),
        "co2_total_tonnes": round(co2_total / 1000, 4),
        "trees_to_offset": round(co2_total / 21),  # avg tree absorbs ~21 kg CO2/year
        "equivalent_km_driving": round(co2_total / 0.192),
    }

@router.get("/driving", summary="Calculate CO2 from driving")
def driving_carbon(
    distance_km: float = Query(..., gt=0),
    vehicle_type: str = Query("gasoline_medium", description="gasoline_small, gasoline_medium, gasoline_large, diesel, hybrid, electric_us, electric_eu, motorcycle"),
    passengers: int = Query(1, ge=1, le=9)
):
    if vehicle_type not in EMISSION_FACTORS["driving"]:
        raise HTTPException(status_code=400, detail=f"vehicle_type must be: {list(EMISSION_FACTORS['driving'].keys())}")
    co2_vehicle = distance_km * EMISSION_FACTORS["driving"][vehicle_type]
    co2_per_person = co2_vehicle / passengers
    return {
        "distance_km": distance_km,
        "vehicle_type": vehicle_type,
        "passengers": passengers,
        "co2_vehicle_kg": round(co2_vehicle, 3),
        "co2_per_person_kg": round(co2_per_person, 3),
        "trees_to_offset": round(co2_vehicle / 21),
    }

@router.get("/electricity", summary="Calculate CO2 from electricity usage")
def electricity_carbon(
    kwh: float = Query(..., gt=0, description="Electricity usage in kWh"),
    region: str = Query("us", description="Region: us, eu, uk, canada, australia, global_average"),
    period: str = Query("monthly", description="Period label: daily, monthly, yearly (informational)")
):
    if region not in EMISSION_FACTORS["electricity"]:
        raise HTTPException(status_code=400, detail=f"region must be: {list(EMISSION_FACTORS['electricity'].keys())}")
    factor = EMISSION_FACTORS["electricity"][region]
    co2 = kwh * factor
    return {
        "kwh": kwh,
        "region": region,
        "period": period,
        "emission_factor_kg_per_kwh": factor,
        "co2_kg": round(co2, 3),
        "co2_tonnes": round(co2 / 1000, 6),
        "trees_to_offset": round(co2 / 21, 2),
    }

@router.get("/diet", summary="Calculate annual CO2 from diet")
def diet_carbon(
    diet_type: str = Query(..., description="vegan, vegetarian, pescatarian, average, high_meat"),
    days: int = Query(365, ge=1, le=3650)
):
    if diet_type not in EMISSION_FACTORS["diet"]:
        raise HTTPException(status_code=400, detail=f"diet_type must be: {list(EMISSION_FACTORS['diet'].keys())}")
    daily = EMISSION_FACTORS["diet"][diet_type]
    co2 = daily * days
    return {
        "diet_type": diet_type,
        "days": days,
        "daily_co2_kg": daily,
        "total_co2_kg": round(co2, 1),
        "total_co2_tonnes": round(co2 / 1000, 3),
        "comparison_vs_average": round((daily / EMISSION_FACTORS["diet"]["average"] - 1) * 100, 1),
    }

@router.get("/food", summary="Calculate CO2 from specific food items")
def food_carbon(
    beef_kg: float = Query(0, ge=0),
    chicken_kg: float = Query(0, ge=0),
    pork_kg: float = Query(0, ge=0),
    cheese_kg: float = Query(0, ge=0),
    milk_liters: float = Query(0, ge=0),
):
    total = (
        beef_kg * EMISSION_FACTORS["beef_kg"] +
        chicken_kg * EMISSION_FACTORS["chicken_kg"] +
        pork_kg * EMISSION_FACTORS["pork_kg"] +
        cheese_kg * EMISSION_FACTORS["cheese_kg"] +
        milk_liters * EMISSION_FACTORS["milk_liter"]
    )
    return {
        "inputs": {"beef_kg": beef_kg, "chicken_kg": chicken_kg, "pork_kg": pork_kg,
                   "cheese_kg": cheese_kg, "milk_liters": milk_liters},
        "total_co2_kg": round(total, 3),
        "breakdown": {
            "beef_co2_kg": round(beef_kg * EMISSION_FACTORS["beef_kg"], 3),
            "chicken_co2_kg": round(chicken_kg * EMISSION_FACTORS["chicken_kg"], 3),
            "pork_co2_kg": round(pork_kg * EMISSION_FACTORS["pork_kg"], 3),
            "cheese_co2_kg": round(cheese_kg * EMISSION_FACTORS["cheese_kg"], 3),
            "milk_co2_kg": round(milk_liters * EMISSION_FACTORS["milk_liter"], 3),
        }
    }
