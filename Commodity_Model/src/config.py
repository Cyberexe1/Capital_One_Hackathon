import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "commodity_prices.csv")  # Prices in quintals
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "features.csv")  # Converted to per kg
MODEL_PATH = os.path.join(BASE_DIR, "models", "xgboost_model.pkl")

# Model params
CUTOFF_DATE = "2024-07-01"
TARGET_COL = "target"
FEATURE_COLS = ["lag_1", "lag_7", "rmean_7", "rstd_7", "weekday", "month"]
