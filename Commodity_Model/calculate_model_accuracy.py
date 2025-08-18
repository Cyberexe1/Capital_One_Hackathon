#!/usr/bin/env python3
"""
Calculate detailed prediction accuracy metrics for the commodity model
"""

import pandas as pd
import joblib
import numpy as np
from src import config
from sklearn.metrics import r2_score, mean_absolute_percentage_error

def calculate_accuracy():
    print("📊 Calculating Model Prediction Accuracy...")
    print("=" * 50)
    
    # Load processed data and model
    df = pd.read_csv(config.PROCESSED_DATA_PATH)
    model = joblib.load(config.MODEL_PATH)
    
    # Split data
    cutoff = pd.Timestamp(config.CUTOFF_DATE)
    df['Arrival_Date'] = pd.to_datetime(df['Arrival_Date'])
    test = df[df['Arrival_Date'] >= cutoff]
    
    # Make predictions
    X_test, y_test = test[config.FEATURE_COLS], test[config.TARGET_COL]
    preds = model.predict(X_test)
    
    # Calculate accuracy metrics
    r2 = r2_score(y_test, preds)
    mape = mean_absolute_percentage_error(y_test, preds)
    accuracy_percentage = (1 - mape) * 100
    
    # Calculate additional metrics
    mae = np.mean(np.abs(preds - y_test))
    rmse = np.sqrt(np.mean((preds - y_test) ** 2))
    
    # Calculate percentage of predictions within different error ranges
    error_pct = np.abs((preds - y_test) / y_test)
    within_5pct = (error_pct <= 0.05).mean() * 100
    within_10pct = (error_pct <= 0.10).mean() * 100
    within_15pct = (error_pct <= 0.15).mean() * 100
    within_20pct = (error_pct <= 0.20).mean() * 100
    
    # Display results
    print(f"🎯 Overall Prediction Accuracy: {accuracy_percentage:.2f}%")
    print(f"📈 R² Score (Explained Variance): {r2:.4f} ({r2*100:.2f}%)")
    print(f"📉 MAPE (Mean Absolute Percentage Error): {mape*100:.2f}%")
    print(f"💰 MAE (Mean Absolute Error): ₹{mae:.2f} per kg")
    print(f"📊 RMSE (Root Mean Square Error): ₹{rmse:.2f} per kg")
    print()
    print("🎯 Prediction Accuracy by Error Range:")
    print(f"   Within ±5%:  {within_5pct:.1f}% of predictions")
    print(f"   Within ±10%: {within_10pct:.1f}% of predictions")
    print(f"   Within ±15%: {within_15pct:.1f}% of predictions")
    print(f"   Within ±20%: {within_20pct:.1f}% of predictions")
    print()
    print(f"📈 Test samples: {len(y_test):,}")
    print(f"💡 Model explains {r2*100:.1f}% of price variance")
    
    return {
        'accuracy_percentage': accuracy_percentage,
        'r2_score': r2,
        'mape': mape,
        'mae': mae,
        'rmse': rmse,
        'within_10pct': within_10pct
    }

if __name__ == "__main__":
    calculate_accuracy()
