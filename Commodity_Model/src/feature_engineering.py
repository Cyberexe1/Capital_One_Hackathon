import pandas as pd
from src import config

def create_features(df):
    gcols = ['Commodity','Market']
    df['target'] = df.groupby(gcols)['Modal_Price'].shift(-1)

    lags = [1,7,14,30]
    for l in lags:
        df[f'lag_{l}'] = df.groupby(gcols)['Modal_Price'].shift(l)

    df['rmean_7'] = df.groupby(gcols)['Modal_Price'].transform(lambda x: x.shift(1).rolling(7, min_periods=1).mean())
    df['rstd_7']  = df.groupby(gcols)['Modal_Price'].transform(lambda x: x.shift(1).rolling(7, min_periods=1).std())

    df['weekday'] = df['Arrival_Date'].dt.weekday
    df['month'] = df['Arrival_Date'].dt.month

    df = df.dropna(subset=['target','lag_1'])
    df.to_csv(config.PROCESSED_DATA_PATH, index=False)
    return df
