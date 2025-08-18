# 🌾 Commodity Price Prediction System

A machine learning-based system for predicting commodity price changes using XGBoost regression. The system provides detailed price forecasts with specific amount changes per kg for the next week.

## 📋 Features

- **Smart Input Processing**: Handles natural language input like "onion price forecast" or "Does tomato price increase"
- **Menu-Driven Interface**: User-friendly menu system for easy navigation
- **Detailed Predictions**: Shows exact price change amounts (₹X per kg increase/decrease)
- **Case-Insensitive Matching**: Works with any capitalization
- **Market Filtering**: Optional market-specific predictions
- **Model Performance Metrics**: View MAE and RMSE scores

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Required packages (see Installation)

### Installation

1. **Clone/Download the project**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Usage

1. **Run the application:**
   ```bash
   python main.py
   ```

2. **Choose from the menu options:**
   - **Option 1**: Train New Model
   - **Option 2**: Make Price Prediction
   - **Option 3**: View Available Commodities
   - **Option 4**: View Model Performance
   - **Option 5**: Exit

## 🔮 Making Predictions

### Input Examples
The system accepts flexible input formats:

✅ **Simple names:**
- `onion`
- `tomato`
- `potato`

✅ **Natural language:**
- `"onion price forecast"`
- `"Does tomato price increase"`
- `"What about potato next week"`

### Sample Output
```
📈 Onion price is likely to INCREASE by ₹15.50 per kg next week.
   Current: ₹45.20/kg → Predicted: ₹60.70/kg
```

```
📉 Tomato price is likely to DECREASE by ₹8.30 per kg next week.
   Current: ₹35.80/kg → Predicted: ₹27.50/kg
```

## 📁 Project Structure

```
Commodity_Model/
├── main.py                 # Menu-driven main application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── data/                  # Data directory
├── models/                # Trained model storage
├── reports/               # Performance metrics
├── notebooks/             # Jupyter notebooks
└── src/                   # Source code modules
    ├── config.py          # Configuration settings
    ├── data_preprocessing.py  # Data cleaning functions
    ├── feature_engineering.py # Feature creation
    ├── model_training.py      # XGBoost model training
    └── utils.py           # Utility functions
```

## 🛠️ Technical Details

### Model
- **Algorithm**: XGBoost Regression
- **Objective**: Predict next period commodity prices
- **Features**: Lag features, moving averages, and market indicators
- **Evaluation**: Mean Absolute Error (MAE) and Root Mean Square Error (RMSE)

### Data Processing
1. **Data Cleaning**: Handle missing values and outliers
2. **Feature Engineering**: Create lag features and rolling statistics
3. **Train/Test Split**: Time-based split using cutoff date
4. **Prediction**: Compare predicted vs current price for trend direction

## 📊 Available Commodities

The system supports predictions for various commodities including:
- Onion, Tomato, Potato
- Apple, Banana, Pomegranate
- Rice, Wheat, Barley
- Various Dals (Arhar, Bengal Gram, etc.)
- And many more...

*Use Option 3 in the menu to see the complete list of available commodities.*

## 🎯 How It Works

1. **Training Phase**: 
   - Loads and cleans historical commodity data
   - Engineers features (lags, moving averages)
   - Trains XGBoost model on historical patterns

2. **Prediction Phase**:
   - Takes user input (commodity name)
   - Extracts commodity name intelligently from natural language
   - Uses trained model to predict next week's price
   - Calculates and displays specific price change amount

## 📈 Performance

The model provides:
- **MAE (Mean Absolute Error)**: Average prediction error in ₹
- **RMSE (Root Mean Square Error)**: Standard deviation of prediction errors
- **Real-time Metrics**: View current model performance via menu

## 🔧 Configuration

Model settings can be adjusted in `src/config.py`:
- Data paths
- Feature columns
- Model parameters
- Cutoff dates

## 🚨 Troubleshooting

**"No matching data found"**
- Check if the commodity name is spelled correctly
- Use Option 3 to view available commodities
- Try different input formats (e.g., "onion" instead of "onions")

**"No trained model found"**
- Run Option 1 to train a new model first
- Ensure the model file exists in the `models/` directory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

---

**Happy Predicting! 🌾📈**
