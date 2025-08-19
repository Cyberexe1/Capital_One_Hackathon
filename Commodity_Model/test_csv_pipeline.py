#!/usr/bin/env python3
"""
Test script to verify CSV-based commodity model pipeline
"""

import pandas as pd
import os
from src.data_preprocessing import load_and_clean
from src.feature_engineering import create_features
from src.model_training import train_model
from src import config

def test_csv_pipeline():
    print("🧪 Testing CSV-based Commodity Model Pipeline")
    print("=" * 50)
    
    # Step 1: Test data loading
    print("\n1️⃣ Testing CSV data loading...")
    try:
        df = load_and_clean()
        print(f"✅ CSV loaded successfully: {len(df):,} rows")
        print(f"📊 Columns: {list(df.columns)}")
        print(f"🌾 Unique commodities: {len(df['Commodity'].unique())}")
        print(f"🏪 Unique markets: {len(df['Market'].unique())}")
        print(f"📅 Date range: {df['Arrival_Date'].min()} to {df['Arrival_Date'].max()}")
        print(f"💰 Price range: ₹{df['Modal_Price'].min():.2f} - ₹{df['Modal_Price'].max():.2f} per kg (converted from quintal)")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return False
    
    # Step 2: Test feature engineering
    print("\n2️⃣ Testing feature engineering...")
    try:
        features_df = create_features(df)
        print(f"✅ Features created: {len(features_df):,} rows after cleaning")
        print(f"📈 Feature columns: {config.FEATURE_COLS}")
        print(f"🎯 Target column: {config.TARGET_COL}")
        
        # Check for missing values
        missing_features = features_df[config.FEATURE_COLS].isnull().sum().sum()
        missing_target = features_df[config.TARGET_COL].isnull().sum()
        print(f"🔍 Missing values - Features: {missing_features}, Target: {missing_target}")
        
    except Exception as e:
        print(f"❌ Error in feature engineering: {e}")
        return False
    
    # Step 3: Test model training
    print("\n3️⃣ Testing model training...")
    try:
        train_model()
        print("✅ Model training completed successfully")
        
        # Check if model file exists
        if os.path.exists(config.MODEL_PATH):
            print(f"✅ Model saved to: {config.MODEL_PATH}")
        else:
            print("❌ Model file not found")
            return False
            
        # Check if metrics file exists
        if os.path.exists("reports/metrics.txt"):
            with open("reports/metrics.txt", "r") as f:
                metrics = f.read().strip()
            print(f"📊 Model metrics:\n{metrics}")
        else:
            print("⚠️ Metrics file not found")
            
    except Exception as e:
        print(f"❌ Error in model training: {e}")
        return False
    
    # Step 4: Test prediction capability
    print("\n4️⃣ Testing prediction capability...")
    try:
        import joblib
        model = joblib.load(config.MODEL_PATH)
        processed_df = pd.read_csv(config.PROCESSED_DATA_PATH)
        
        # Get test data
        cutoff = pd.Timestamp(config.CUTOFF_DATE)
        processed_df['Arrival_Date'] = pd.to_datetime(processed_df['Arrival_Date'])
        test_data = processed_df[processed_df['Arrival_Date'] >= cutoff]
        
        if not test_data.empty:
            X_test = test_data[config.FEATURE_COLS]
            predictions = model.predict(X_test)
            print(f"✅ Predictions generated for {len(predictions)} samples")
            print(f"📈 Prediction range: ₹{predictions.min():.2f} - ₹{predictions.max():.2f}")
        else:
            print("⚠️ No test data available for predictions")
            
    except Exception as e:
        print(f"❌ Error in prediction testing: {e}")
        return False
    
    print("\n🎉 CSV Pipeline Test Complete!")
    print("=" * 50)
    print("✅ All components working correctly with CSV data")
    print("🚀 Ready to use: python main.py")
    
    return True

if __name__ == "__main__":
    test_csv_pipeline()
