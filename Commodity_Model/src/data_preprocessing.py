import pandas as pd
from src import config

def load_and_clean():
    df = pd.read_csv(config.RAW_DATA_PATH)
    df['Arrival_Date'] = pd.to_datetime(df['Arrival_Date'], dayfirst=True)
    
    # Convert prices from quintal to per kg (1 quintal = 100 kg)
    price_cols = ['Min_Price', 'Max_Price', 'Modal_Price']
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col] / 100  # Convert quintal to per kg
    
    df = df.sort_values(['Commodity','Market','Arrival_Date']).reset_index(drop=True)
    return df
