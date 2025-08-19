import os
import sys
from typing import Optional, Dict, Any

BASE_DIR = os.path.dirname(__file__)
MODEL2_DIR = os.path.join(BASE_DIR, "Model2")
if MODEL2_DIR not in sys.path:
    sys.path.append(MODEL2_DIR)

from cities import CITIES_UP  # type: ignore
from config import LATITUDE, LONGITUDE  # type: ignore
from openweather_client import get_weather_forecast_for  # type: ignore
from crop_model import CropRecommender  # type: ignore
from irrigation_logic import should_irrigate  # type: ignore
from yield_risk_logic import cold_risk_warning  # type: ignore


def _find_city_by_name(name: str):
    name_norm = name.strip().lower()
    for c in CITIES_UP:
        if c["name"].lower() == name_norm:
            return c
    for c in CITIES_UP:
        if c["name"].lower().startswith(name_norm):
            return c
    return None


def get_advisory(city: Optional[str], ph: float) -> Dict[str, Any]:
    """
    Build smart farming advisory for a city and soil pH.

    Returns keys:
    - ok: bool
    - city: str
    - coordinates: {lat, lon}
    - weather: subset of current weather used
    - crop_recommendation: str
    - irrigation_advice: str
    - cold_risk: str
    """
    try:
        ph_val = float(ph)
    except Exception:
        return {"ok": False, "error": "Invalid pH value"}

    sel = _find_city_by_name(city) if city else None
    if sel is None:
        lat, lon = LATITUDE, LONGITUDE
        city_name = city or "Default"
    else:
        lat, lon = sel["lat"], sel["lon"]
        city_name = sel["name"]

    forecast = get_weather_forecast_for(lat, lon)
    if not forecast:
        return {"ok": False, "error": "Failed to fetch weather forecast"}

    # Extract features
    try:
        temperature = float(forecast["current"]["temp"])
        humidity = float(forecast["current"]["humidity"])
    except Exception:
        return {"ok": False, "error": "Weather data missing temp/humidity"}

    rainfall = 0.0
    try:
        if "daily" in forecast and len(forecast["daily"]) > 0:
            rainfall = float(forecast["daily"][0].get("rain", 0.0))
    except Exception:
        rainfall = 0.0

    # Crop model
    dataset_path = os.path.join(MODEL2_DIR, "Crop_recommendation.csv")
    try:
        model = CropRecommender(dataset_path)
        crop = model.predict(
            temperature=temperature, humidity=humidity, rainfall=rainfall, ph=ph_val
        )
    except Exception as e:
        crop = f"Unknown (error: {e})"

    irrigation_advice = should_irrigate(forecast)
    cold_risk = cold_risk_warning(forecast, crop)

    return {
        "ok": True,
        "city": city_name,
        "coordinates": {"lat": lat, "lon": lon},
        "weather": {
            "temperature_c": temperature,
            "humidity_pct": humidity,
            "rainfall_mm": rainfall,
        },
        "inputs": {"ph": ph_val},
        "crop_recommendation": crop,
        "irrigation_advice": irrigation_advice,
        "cold_risk": cold_risk,
    }
