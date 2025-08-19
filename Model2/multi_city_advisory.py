# multi_city_advisory.py
from cities import CITIES_UP
from openweather_client import get_weather_forecast_for
from irrigation_logic import should_irrigate
from yield_risk_logic import cold_risk_warning
from crop_model import CropRecommender

HEADER = "=== 🌾 Smart Farming Advisory (Uttar Pradesh) ===\n"
SEPARATOR = "-" * 60
RECOMMENDER = CropRecommender("Crop_recommendation.csv")


def _extract_features_from_forecast(forecast):
    """Return (temperature, humidity, rainfall) from OpenWeather One Call JSON."""
    # temperature and humidity from current
    current = forecast.get("current", {})
    temp = float(current.get("temp", 0.0))
    humidity = float(current.get("humidity", 0.0))

    # rainfall: prefer today's daily rain, fallback to 0
    daily = forecast.get("daily", [])
    if daily and isinstance(daily, list):
        today = daily[0]
        rainfall = float(today.get("rain", 0.0))
    else:
        rainfall = 0.0

    return temp, humidity, rainfall


def advisory_for_city(city, ph):
    name = city["name"]
    lat = city["lat"]
    lon = city["lon"]

    forecast = get_weather_forecast_for(lat, lon)
    if not forecast:
        return f"{name}: ❌ Could not fetch forecast."

    temp, humidity, rainfall = _extract_features_from_forecast(forecast)
    crop = RECOMMENDER.predict(temp, humidity, rainfall, ph)
    irrigation = should_irrigate(forecast)
    cold = cold_risk_warning(forecast, crop)

    lines = [
        f"City: {name} ({lat}, {lon})",
        f"✅ Recommended Crop: {crop}",
        f"💧 Irrigation: {irrigation}",
        f"❄ Cold Risk: {cold}",
    ]
    return "\n".join(lines)


def find_city_by_name(name: str):
    name_norm = name.strip().lower()
    # Exact match first
    for c in CITIES_UP:
        if c["name"].lower() == name_norm:
            return c
    # Startswith fallback
    for c in CITIES_UP:
        if c["name"].lower().startswith(name_norm):
            return c
    return None


def main():
    print(HEADER)
    available = ", ".join(c["name"] for c in CITIES_UP)
    user_in = input(
        "Enter city name(s) from Uttar Pradesh (comma-separated), or 'all' for all cities\n"
        f"Available: {available}\n> "
    ).strip()

    # Prompt once for soil pH for dataset-based prediction
    while True:
        ph_in = input("Enter soil pH (e.g., 6.5): ").strip()
        try:
            ph = float(ph_in)
            break
        except ValueError:
            print("Please enter a valid number for pH.")

    selected = []
    if user_in.lower() == "all":
        selected = CITIES_UP
    else:
        parts = [p for p in (x.strip() for x in user_in.split(",")) if p]
        for p in parts:
            city = find_city_by_name(p)
            if city:
                selected.append(city)
            else:
                print(f"⚠️  City not found: {p}")

    if not selected:
        print("No valid cities selected. Exiting.")
        return

    count = 0
    for city in selected:
        print(SEPARATOR)
        print(advisory_for_city(city, ph))
        count += 1
    print(f"\n=== ✅ Advisory Generated for {count} city(ies) ===")


if __name__ == "__main__":
    main()
