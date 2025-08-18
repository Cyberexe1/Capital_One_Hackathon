# openweather_client.py
import requests
from config import OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL, LATITUDE, LONGITUDE

def get_weather_forecast():
    params = {
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "exclude": "minutely,hourly,alerts"
    }
    try:
        response = requests.get(OPENWEATHER_BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] OpenWeather API failed: {e}")
        return None

def get_weather_forecast_for(lat, lon):
    """Fetch forecast for given coordinates using One Call 3.0."""
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "exclude": "minutely,hourly,alerts"
    }
    try:
        response = requests.get(OPENWEATHER_BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] OpenWeather API failed for {lat},{lon}: {e}")
        return None
