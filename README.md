# MICK – AI Speech Assistant for Agriculture

An end-to-end Django web app that helps farmers with:
- Commodity price trends (predicts next-week price and change)
- Smart farming advisory (seed/crop recommendation, irrigation timing, cold-risk)
- Voice-first UX with speech input and text-to-speech output (Sarvam TTS)

Frontend is a single page at `template/index.html` with rich UI and keyboard shortcuts. Backend provides JSON APIs in `agri_api/` and project-level endpoints in `base/`.

---

## Tech Stack
- Django 5.x (`manage.py`, project in `base/`)
- Python (tested with 3.11+)
- Frontend: Vanilla JS/CSS in `static/` (`scripts/script.js`, `scripts/chat.js`, `styles/styles.css`)
- ML models and data pipelines:
  - Price prediction in `Commodity_Model/` (served via `commodity_price.py`)
  - Advisory (weather + crop model) in `Model2/` (served via `smart_farming.py`)

---

## Project Layout
- `manage.py` – Django entrypoint
- `base/` – Django project (settings, urls, views)
- `agri_api/` – API endpoints for price, advisory, and TTS
- `template/index.html` – main UI page
- `static/` – JS/CSS assets
- `commodity_price.py` – wraps commodity model for price predictions
- `smart_farming.py` – wraps weather + crop models for advisory
- `Commodity_Model/` – ML artifacts (see its README)
- `Model2/` – advisory components and configs (see `README_NEW.md`)

---

## Features
- Voice and text input with real-time UI feedback
- Price trend for a commodity with current vs predicted price (per kg and per quintal)
- Smart advisory combining weather forecast and soil pH
- Hindi/English handling with translation fallback (LibreTranslate)
- Sarvam TTS passthrough for natural voice responses

---

## Environment Variables
Set via system env or a local `.env` (loaded in `base/settings.py`).

- Django
  - `SECRET_KEY` – Django secret key (default dev key present; override in prod)
  - `DEBUG` – `true/false` (defaults to true)

- Translation
  - `TRANSLATE_URL` – optional, defaults to `https://libretranslate.de/translate`

- Sarvam TTS (backend passthrough in `agri_api/views.py` and `base/views.py`)
  - `SARVAM_API_KEY` – required to enable TTS server-side
  - `SARVAM_TTS_URL` – optional; defaults to `https://api.sarvam.ai/text-to-speech`

- Smart Farming Advisory (Model2)
  - OpenWeather is read from `Model2/config.py` (currently hardcoded):
    - `OPENWEATHER_API_KEY`
    - `OPENWEATHER_BASE_URL` (default `https://api.openweathermap.org/data/3.0/onecall`)
    - `LATITUDE`, `LONGITUDE` (defaults point to Varanasi)
  - Recommendation: refactor to read from env (e.g., `OPENWEATHER_API_KEY`) before production.

---

## Installation
1) Create and activate a virtual environment
```bash
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) (Optional) Create `.env` at project root
```env
SECRET_KEY=your-secret
DEBUG=true
SARVAM_API_KEY=your-sarvam-key
SARVAM_TTS_URL=https://api.sarvam.ai/text-to-speech
TRANSLATE_URL=https://libretranslate.de/translate
```

4) Database setup
```bash
python manage.py migrate
```

5) Run the server
```bash
python manage.py runserver
```
Visit http://127.0.0.1:8000/

---

## API Endpoints
Base router: `base/base/urls.py` and `agri_api/urls.py`.

- App index
  - `GET /` – renders `index.html`

- Price
  - `GET /api/price/?commodity=<name>&market=<city?>`
    - returns one commodity’s predicted price
  - `GET /api/price/all/?market=<city?>&q=<filter?>`
    - returns all commodities; `q` narrows to best match

- Advisory
  - `GET /api/advisory/?city=<name>&ph=<float>`
    - returns JSON advisory with `crop_recommendation`, `irrigation_advice`, `cold_risk`

- Speech and TTS
  - `POST /api/process-speech/` – deterministic NLP fallback pipeline
    - body: `{ "spoken_text": "...", "language": "hi-IN|en-US|..." }`
    - returns `{ success, chatbot_response }`
  - `POST /api/text-to-speech/` – Sarvam passthrough
    - body: `{ "text": "...", "language": "hi-IN|en-IN", "voice": "Anushka" }`
    - returns `{ success, audio_base64 }`

---

## Frontend Usage
- Open `/` in the browser
- Click the “MIC” circle or press SPACE to start listening
- Type and press ENTER to send text
- Press `0` to replay last response
- Toggle Settings to change voice speed and auto-speak

Note: `template/index.html` includes DEV-ONLY inline keys for Gemini and Sarvam:
- `window.GEMINI_API_KEY` and `window.SARVAM_API_KEY` are hard-coded for local testing. Remove these before any public sharing or deployment.

---

## Price Prediction Details
- Served by `commodity_price.py` which loads model/data paths from `Commodity_Model/src/config.py`
- Response example:
```json
{
  "ok": true,
  "commodity": "onion",
  "market": "Varanasi",
  "current_price": 16.75,
  "predicted_price": 18.20,
  "change": 1.45,
  "trend": "increase",
  "current_price_quintal": 1675.0,
  "predicted_price_quintal": 1820.0
}
```

- Bulk list: `GET /api/price/all/` returns `{ ok, count, items: [...] }`

---

## Advisory Details
- `smart_farming.py` orchestrates:
  - Weather from OpenWeather One Call 3.0
  - Crop recommendation using `Model2/Crop_recommendation.csv` via `CropRecommender`
  - Irrigation recommendation and cold-risk via `Model2/`
- Example call:
```bash
curl "http://127.0.0.1:8000/api/advisory/?city=Varanasi&ph=6.5"
```

---

## Development Notes
- Static files path is configured in `base/settings.py` with `STATICFILES_DIRS = [BASE_DIR / "static"]`
- Templates directory is `BASE_DIR / "template"`
- CSRF: frontend JS fetches include `X-CSRFToken` via `getCookie('csrftoken')`
- Translation fallback uses LibreTranslate public endpoint; consider self-hosting for reliability

---

## Security & Production
- Do not expose API keys in client code (`template/index.html`). Use backend proxies and server-side env vars.
- Set `DEBUG=false` and configure `ALLOWED_HOSTS` in `base/settings.py` for production.
- Move OpenWeather key into environment variables and remove from `Model2/config.py`.
- Serve static files via CDN or proper web server in production.

---

## Troubleshooting
- Price endpoints error: ensure `Commodity_Model/models/xgboost_model.pkl` and processed CSV paths exist per `Commodity_Model/src/config.py`.
- Advisory errors: set a valid `OPENWEATHER_API_KEY` and ensure internet access.
- TTS errors: set `SARVAM_API_KEY`; verify `SARVAM_TTS_URL` matches the provider endpoint.
- CORS/403 from direct TTS: set `window.USE_DIRECT_SARVAM = false` (default) to force backend proxy.

---

## License
Internal/Project use. Add a license file if distributing.
