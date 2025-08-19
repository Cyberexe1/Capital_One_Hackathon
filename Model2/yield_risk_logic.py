# yield_risk_logic.py

def cold_risk_warning(forecast_data, crop_name):
    crop_min_temp = {
        "Rice": 15,
        "Millet": 20,
        "Wheat": 5,
        "Maize": 10
    }

    min_temp_threshold = crop_min_temp.get(crop_name, 10)

    try:
        next_week_mins = [day["temp"]["min"] for day in forecast_data.get("daily", [])[:7]]
        risky_days = [temp for temp in next_week_mins if temp < min_temp_threshold]

        if risky_days:
            return f"⚠ Cold risk detected: {len(risky_days)} days below {min_temp_threshold}°C may harm {crop_name}."
        else:
            return f"No significant cold risk for {crop_name} in the next week."
    except KeyError:
        return "Error checking cold risk."
