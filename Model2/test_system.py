# test_system.py - Simple test to verify the system works
from openweather_client import get_weather_forecast
from irrigation_logic import should_irrigate
from yield_risk_logic import cold_risk_warning
from crop_model import CropRecommender

print("=== 🌾 Testing Smart Farming System ===\n")

# Test OpenWeather API
print("1. Testing OpenWeather API...")
forecast_data = get_weather_forecast()
if forecast_data:
    print("✅ OpenWeather API: Working")
    current_temp = forecast_data.get("current", {}).get("temp", "N/A")
    print(f"   Current temperature: {current_temp}°C")
else:
    print("❌ OpenWeather API: Failed")

print()

def _extract_features_from_forecast(forecast):
    current = forecast.get("current", {})
    temp = float(current.get("temp", 0.0))
    humidity = float(current.get("humidity", 0.0))
    daily = forecast.get("daily", [])
    if daily and isinstance(daily, list):
        today = daily[0]
        rainfall = float(today.get("rain", 0.0))
    else:
        rainfall = 0.0
    return temp, humidity, rainfall


# Test crop recommendation with dataset model
print("2. Testing crop recommendation (dataset model)...")
recommender = CropRecommender("Crop_recommendation.csv")
if forecast_data:
    temp, humidity, rainfall = _extract_features_from_forecast(forecast_data)
    # Use a sample pH; adjust as needed or prompt interactively
    ph = 6.5
    crop = recommender.predict(temp, humidity, rainfall, ph)
    print(f"✅ Recommended Crop: {crop}")
else:
    crop = "Maize"  # fallback
    print(f"⚠️  Using fallback crop: {crop}")

print()

# Test irrigation advice
print("3. Testing irrigation advice...")
irrigation_advice = should_irrigate(forecast_data)
print(f"💧 Irrigation: {irrigation_advice}")

print()

# Test cold risk assessment
print("4. Testing cold risk assessment...")
cold_risk = cold_risk_warning(forecast_data, crop)
print(f"❄️ Cold Risk: {cold_risk}")

print("\n=== ✅ Test Complete ===")
