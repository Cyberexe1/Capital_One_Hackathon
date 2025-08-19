# irrigation_logic.py

def should_irrigate(forecast_data):
    if not forecast_data:
        return "No forecast data to decide irrigation."

    try:
        next_3_days_rain = sum(day.get("rain", 0) for day in forecast_data.get("daily", [])[:3])
        if next_3_days_rain < 5:
            return "Irrigate soon — very little rain expected in the next 3 days."
        else:
            return "No need to irrigate now — rain expected soon."
    except KeyError:
        return "Error processing forecast data for irrigation."
