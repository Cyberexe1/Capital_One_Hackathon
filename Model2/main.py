# main.py
from openweather_client import get_weather_forecast_for
from irrigation_logic import should_irrigate
from yield_risk_logic import cold_risk_warning
from cities import CITIES_UP
from config import LATITUDE, LONGITUDE
from crop_model import CropRecommender
import os


def find_city_by_name(name: str):
    name_norm = name.strip().lower()
    # exact match
    for c in CITIES_UP:
        if c["name"].lower() == name_norm:
            return c
    # startswith fallback
    for c in CITIES_UP:
        if c["name"].lower().startswith(name_norm):
            return c
    return None

if __name__ == "__main__":
    print("=== 🌾 Smart Farming Advisory ===\n")

    # Ask user for city
    available = ", ".join(c["name"] for c in CITIES_UP)
    city_in = input(
        "Enter a city in Uttar Pradesh for advisory\n"
        f"Available: {available}\n> "
    ).strip()

    sel = find_city_by_name(city_in) if city_in else None
    if sel is None:
        print("⚠️  City not found. Using default coordinates from config.")
        lat, lon = LATITUDE, LONGITUDE
        city_name = "Default"
    else:
        lat, lon = sel["lat"], sel["lon"]
        city_name = sel["name"]

    print(f"\n📍 City: {city_name} ({lat}, {lon})\n")

    # Fetch forecast for selected city
    forecast_data = get_weather_forecast_for(lat, lon)
    if not forecast_data:
        print("❌ Failed to fetch forecast. Exiting.")
        exit(1)

    # Ask user for soil pH
    while True:
        ph_in = input("Enter soil pH value (e.g., 6.5): ").strip()
        try:
            ph_value = float(ph_in)
            break
        except ValueError:
            print("Invalid pH. Please enter a numeric value.")

    # Extract features from forecast
    try:
        temperature = float(forecast_data["current"]["temp"])  # °C
        humidity = float(forecast_data["current"]["humidity"])  # %
    except (KeyError, TypeError, ValueError):
        print("❌ Could not extract temperature/humidity from forecast. Exiting.")
        exit(1)

    # Daily rainfall for day 0 (mm), default 0 if missing
    rainfall = 0.0
    try:
        if "daily" in forecast_data and len(forecast_data["daily"]) > 0:
            rainfall = float(forecast_data["daily"][0].get("rain", 0.0))
    except (TypeError, ValueError):
        rainfall = 0.0

    # 1️⃣ Question 1: Crop recommendation using dataset model
    dataset_path = os.path.join(os.path.dirname(__file__), "Crop_recommendation.csv")
    try:
        model = CropRecommender(dataset_path)
        crop = model.predict(temperature=temperature, humidity=humidity, rainfall=rainfall, ph=ph_value)
    except Exception as e:
        print(f"❌ Crop model error: {e}")
        crop = "Unknown"

    print(f"Q1: What seed variety suits this unpredictable weather?")
    print(f"✅ Recommended Crop: {crop}\n")

    # 3️⃣ Question 2: When should I irrigate?
    irrigation_advice = should_irrigate(forecast_data)
    print(f"Q2: When should I irrigate?")
    print(f"💧 Advice: {irrigation_advice}\n")

    # 4️⃣ Question 3: Will next week's temperature drop kill my yield?
    cold_risk = cold_risk_warning(forecast_data, crop)
    print(f"Q3: Will next week's temperature drop kill my yield?")
    print(f"❄ Risk Assessment: {cold_risk}\n")

    print("=== ✅ Advisory Complete ===")
