# Smart Farming Advisory (Uttar Pradesh)

A concise advisory system for Uttar Pradesh cities using OpenWeather One Call 3.0 and a dataset-driven crop recommendation.

It answers:
- What seed variety suits current weather? (dataset model on temperature, humidity, rainfall, pH)
- When should I irrigate? (3-day rainfall forecast)
- Will next week's temperature drop harm my yield? (cold risk)

## Features
- Interactive city selection in `main.py` from `cities.py`
- Prompts for soil pH, then predicts crop from `Crop_recommendation.csv`
- Multi-city interactive advisory via `multi_city_advisory.py`
- OpenWeather-only workflow (no Ambee dependency for crop suggestion)

## Requirements
- Python 3.10+
- Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration
Set your OpenWeather API key in `config.py`:
```python
OPENWEATHER_API_KEY = "YOUR_OPENWEATHER_KEY"
```

## Dataset
- File: `Crop_recommendation.csv`
- Required columns: `temperature`, `humidity`, `rainfall`, `ph`, `label`
- Model: KNN (see `crop_model.py`)

## Usage
- Single city (interactive):
```bash
python main.py
```
Follow prompts:
1) Choose a city (from `cities.py`, e.g., Lucknow, Kanpur, Varanasi, Agra, Prayagraj, Ghaziabad, Noida, Meerut, Bareilly, Gorakhpur)
2) Enter soil pH (e.g., 6.5)

- Multiple cities (interactive):
```bash
python multi_city_advisory.py
```
Enter one or more cities separated by commas, or `all` to run for all.

## How it works
- `main.py` pulls current `temperature` and `humidity`, and today's `rainfall` from OpenWeather for the selected city.
- You provide `pH`.
- `crop_model.py` loads `Crop_recommendation.csv`, trains KNN, and predicts the crop.
- `irrigation_logic.py` sums next-3-days rainfall for irrigation advice.
- `yield_risk_logic.py` checks a 7-day min-temperature risk by crop.

## Project Structure
- `main.py` — Interactive single-city advisory with dataset crop prediction
- `multi_city_advisory.py` — Multi-city advisory (OpenWeather based)
- `crop_model.py` — KNN model for dataset-driven crop recommendation
- `cities.py` — UP city list with coordinates
- `openweather_client.py` — OpenWeather One Call 3.0 client
- `irrigation_logic.py` — Irrigation timing logic
- `yield_risk_logic.py` — Cold risk assessment
- `config.py` — API keys and defaults

## Notes
- A scikit-learn warning about feature names may appear; it's harmless in this workflow.
- Ensure good internet connectivity and a valid `OPENWEATHER_API_KEY`.
- You can expand `cities.py` with more cities anytime.
