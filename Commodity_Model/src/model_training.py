import pandas as pd
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb
from src import config
import numpy as np

def train_model():
    df = pd.read_csv(config.PROCESSED_DATA_PATH)
    cutoff = pd.Timestamp(config.CUTOFF_DATE)

    df['Arrival_Date'] = pd.to_datetime(df['Arrival_Date'])
    train = df[df['Arrival_Date'] < cutoff]
    test = df[df['Arrival_Date'] >= cutoff]

    X_train, y_train = train[config.FEATURE_COLS], train[config.TARGET_COL]
    X_test, y_test = test[config.FEATURE_COLS], test[config.TARGET_COL]

    model = xgb.XGBRegressor(objective='reg:squarederror', n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))

    with open("reports/metrics.txt", "w") as f:
        f.write(f"MAE: {mae}\nRMSE: {rmse}\n")

    joblib.dump(model, config.MODEL_PATH)
    print(f"Model saved to {config.MODEL_PATH}")
    print(f"MAE: {mae}, RMSE: {rmse}")
