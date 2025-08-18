from src.data_preprocessing import load_and_clean
from src.feature_engineering import create_features
from src.model_training import train_model
import pandas as pd
import joblib
from src import config

def show_menu():
    print("\n" + "="*50)
    print("🌾 COMMODITY PRICE PREDICTION SYSTEM 🌾")
    print("="*50)
    print("1. Train New Model")
    print("2. Make Price Prediction")
    print("3. View Available Commodities")
    print("4. View Model Performance")
    print("5. Exit")
    print("="*50)

def train_new_model():
    print("\n📊 Training new model...")
    print("Loading and cleaning data...")
    df = load_and_clean()

    print("Creating features...")
    create_features(df)

    print("Training model...")
    train_model()

    print("✅ Model training complete!")

def make_prediction():
    print("\n🔮 Making price prediction...")
    
    # Load the trained model
    try:
        model = joblib.load(config.MODEL_PATH)
        df = pd.read_csv(config.PROCESSED_DATA_PATH)
        print("✅ Model loaded successfully!")
    except FileNotFoundError:
        print("❌ No trained model found. Please train a model first (Option 1).")
        return

    # Get latest data for prediction
    cutoff = pd.Timestamp(config.CUTOFF_DATE)
    df['Arrival_Date'] = pd.to_datetime(df['Arrival_Date'])
    test = df[df['Arrival_Date'] >= cutoff]
    
    if test.empty:
        print("❌ No test data available for predictions.")
        return

    # Make predictions
    X_test = test[config.FEATURE_COLS]
    preds = model.predict(X_test)
    
    latest_test = test.copy()
    latest_test['Predicted'] = preds
    latest_test['Price_Change'] = latest_test['Predicted'] > latest_test['lag_1']

    # Get user input for commodity
    commodity_input = input("\nEnter commodity name (e.g., Onion): ").strip().lower()
    market_input = input("Enter market name (or press Enter to skip): ").strip()

    # Extract commodity name from user's input
    available_commodities = latest_test['Commodity'].str.lower().unique()
    commodity_name = None
    
    # First try exact match with first word
    first_word = commodity_input.split()[0] if commodity_input else ""
    if first_word in available_commodities:
        commodity_name = first_word
    else:
        # Look for any commodity name in the input
        for commodity in available_commodities:
            if commodity in commodity_input:
                commodity_name = commodity
                break
    
    if not commodity_name:
        print(f"❌ Could not find a valid commodity in your input: '{commodity_input}'")
        print(f"💡 Available commodities: {', '.join(sorted(available_commodities))}")
        return

    # Filter by commodity and market
    if market_input:
        mask = (latest_test['Commodity'].str.lower() == commodity_name) & \
               (latest_test['Market'].str.lower() == market_input.lower())
    else:
        mask = (latest_test['Commodity'].str.lower() == commodity_name)

    if mask.sum() == 0:
        print("❌ No matching data found for your input.")
        return

    # Get prediction result with actual price change amount
    latest_row = latest_test[mask].sort_values('Arrival_Date').iloc[-1]
    
    # Calculate the predicted price change amount
    current_price = latest_row['lag_1']  # Current price (previous period)
    predicted_price = latest_row['Predicted']  # Next period predicted price
    price_change = predicted_price - current_price
    
    # Display the prediction with specific amount (converted from quintal to per kg)
    if price_change > 0:
        print(f"📈 {commodity_name.title()} price is likely to INCREASE by ₹{abs(price_change):.2f} per kg next week.")
        print(f"   Current: ₹{current_price:.2f}/kg → Predicted: ₹{predicted_price:.2f}/kg")
        print(f"   (Original data: ₹{current_price*100:.0f}/quintal → ₹{predicted_price*100:.0f}/quintal)")
    else:
        print(f"📉 {commodity_name.title()} price is likely to DECREASE by ₹{abs(price_change):.2f} per kg next week.")
        print(f"   Current: ₹{current_price:.2f}/kg → Predicted: ₹{predicted_price:.2f}/kg")
        print(f"   (Original data: ₹{current_price*100:.0f}/quintal → ₹{predicted_price*100:.0f}/quintal)")

def view_commodities():
    print("\n📋 Available Commodities...")
    try:
        df = pd.read_csv(config.PROCESSED_DATA_PATH)
        commodities = sorted(df['Commodity'].unique())
        print(f"\n🌾 Total commodities: {len(commodities)}")
        print("-" * 30)
        for i, commodity in enumerate(commodities, 1):
            print(f"{i:2d}. {commodity}")
    except FileNotFoundError:
        print("❌ No data file found. Please train a model first (Option 1).")

def view_performance():
    print("\n📊 Model Performance Metrics...")
    try:
        with open("reports/metrics.txt", "r") as f:
            metrics = f.read()
        print("✅ Latest model performance:")
        print("-" * 30)
        print(metrics)
    except FileNotFoundError:
        print("❌ No performance metrics found. Please train a model first (Option 1).")

def main():
    while True:
        show_menu()
        try:
            choice = input("\nSelect an option (1-5): ").strip()
            
            if choice == '1':
                train_new_model()
            elif choice == '2':
                make_prediction()
            elif choice == '3':
                view_commodities()
            elif choice == '4':
                view_performance()
            elif choice == '5':
                print("\n👋 Thank you for using Commodity Price Prediction System!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
