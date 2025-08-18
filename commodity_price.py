import os
import sys
from typing import Optional, Dict, Any

# Ensure Commodity_Model modules are importable (they expect `src` at sys.path)
BASE_DIR = os.path.dirname(__file__)
COMMODITY_DIR = os.path.join(BASE_DIR, "Commodity_Model")
if COMMODITY_DIR not in sys.path:
    sys.path.append(COMMODITY_DIR)

import pandas as pd  # type: ignore
import joblib  # type: ignore
from src import config  # type: ignore


def predict_price(commodity: str, market: Optional[str] = None) -> Dict[str, Any]:
    """
    Predict next week's price for a commodity (optionally filtered by market).

    Returns a dictionary suitable for JSON serialization.
    """
    if not commodity or not isinstance(commodity, str):
        return {
            "ok": False,
            "error": "commodity is required",
        }

    try:
        model = joblib.load(config.MODEL_PATH)
        df = pd.read_csv(config.PROCESSED_DATA_PATH)
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "Trained model or processed data not found. Please train the model first.",
        }
    except Exception as e:
        return {"ok": False, "error": f"Failed to load model/data: {e}"}

    cutoff = pd.Timestamp(config.CUTOFF_DATE)
    try:
        df["Arrival_Date"] = pd.to_datetime(df["Arrival_Date"])  # may raise if missing
    except Exception as e:
        return {"ok": False, "error": f"Invalid Arrival_Date in data: {e}"}

    test = df[df["Arrival_Date"] >= cutoff]
    if test.empty:
        return {"ok": False, "error": "No recent data available for predictions."}

    X_test = test[config.FEATURE_COLS]
    try:
        preds = model.predict(X_test)
    except Exception as e:
        return {"ok": False, "error": f"Model prediction failed: {e}"}

    latest_test = test.copy()
    latest_test["Predicted"] = preds

    # Normalize inputs
    commodity_norm = commodity.strip().lower()
    market_norm = market.strip().lower() if market else None

    # Commodity matching similar to CLI behavior
    available = latest_test["Commodity"].astype(str).str.lower().unique()
    commodity_name = None
    if commodity_norm:
        first_word = commodity_norm.split()[0]
        if first_word in available:
            commodity_name = first_word
        else:
            for c in available:
                if c in commodity_norm:
                    commodity_name = c
                    break

    if not commodity_name:
        return {
            "ok": False,
            "error": f"Commodity not found: {commodity}",
            "available": sorted(map(str, available)),
        }

    if market_norm:
        mask = (
            latest_test["Commodity"].astype(str).str.lower() == commodity_name
        ) & (latest_test["Market"].astype(str).str.lower() == market_norm)
    else:
        mask = latest_test["Commodity"].astype(str).str.lower() == commodity_name

    if mask.sum() == 0:
        return {"ok": False, "error": "No matching rows for given commodity/market"}

    latest_row = latest_test[mask].sort_values("Arrival_Date").iloc[-1]

    current_price = float(latest_row["lag_1"])  # per kg
    predicted_price = float(latest_row["Predicted"])  # per kg
    price_change = predicted_price - current_price

    trend = "increase" if price_change > 0 else ("no_change" if price_change == 0 else "decrease")

    return {
        "ok": True,
        "commodity": commodity_name,
        "market": market if market else None,
        "current_price": round(current_price, 2),
        "predicted_price": round(predicted_price, 2),
        "change": round(price_change, 2),
        "trend": trend,
        # Additional metadata (original quintal scale for reference)
        "current_price_quintal": round(current_price * 100, 2),
        "predicted_price_quintal": round(predicted_price * 100, 2),
    }


def predict_all_prices(market: Optional[str] = None) -> Dict[str, Any]:
    """
    Predict next week's price for all available commodities (optionally filtered by market).

    Returns a dict with ok, count, and items (list of per-commodity results
    using the same fields as predict_price())
    """
    try:
        model = joblib.load(config.MODEL_PATH)
        df = pd.read_csv(config.PROCESSED_DATA_PATH)
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "Trained model or processed data not found. Please train the model first.",
        }
    except Exception as e:
        return {"ok": False, "error": f"Failed to load model/data: {e}"}

    cutoff = pd.Timestamp(config.CUTOFF_DATE)
    try:
        df["Arrival_Date"] = pd.to_datetime(df["Arrival_Date"])
    except Exception as e:
        return {"ok": False, "error": f"Invalid Arrival_Date in data: {e}"}

    test = df[df["Arrival_Date"] >= cutoff]
    if test.empty:
        return {"ok": False, "error": "No recent data available for predictions."}

    X_test = test[config.FEATURE_COLS]
    try:
        preds = model.predict(X_test)
    except Exception as e:
        return {"ok": False, "error": f"Model prediction failed: {e}"}

    latest_test = test.copy()
    latest_test["Predicted"] = preds

    # If market specified, filter rows by market first
    market_norm = market.strip().lower() if isinstance(market, str) and market else None
    if market_norm:
        latest_test = latest_test[
            latest_test["Market"].astype(str).str.lower() == market_norm
        ]
        if latest_test.empty:
            return {"ok": True, "count": 0, "items": []}

    # For each commodity, pick most recent row and compute metrics
    items = []
    for commodity_name, group in latest_test.groupby(latest_test["Commodity"].astype(str).str.lower()):
        row = group.sort_values("Arrival_Date").iloc[-1]
        current_price = float(row["lag_1"])  # per kg
        predicted_price = float(row["Predicted"])  # per kg
        price_change = predicted_price - current_price
        trend = (
            "increase" if price_change > 0 else ("no_change" if price_change == 0 else "decrease")
        )
        items.append({
            "commodity": commodity_name,
            "market": market if market else None,
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "change": round(price_change, 2),
            "trend": trend,
            "current_price_quintal": round(current_price * 100, 2),
            "predicted_price_quintal": round(predicted_price * 100, 2),
        })

    # Sort items by commodity name for consistency
    items.sort(key=lambda x: x["commodity"]) 
    return {"ok": True, "count": len(items), "items": items}
