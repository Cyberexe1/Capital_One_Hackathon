# crop_model.py
import os
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

class CropRecommender:
    def __init__(self, csv_path: str, n_neighbors: int = 5):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Dataset not found: {csv_path}")
        self.csv_path = csv_path
        self.n_neighbors = n_neighbors
        self.scaler = StandardScaler()
        self.model = None
        self._train()

    def _train(self):
        df = pd.read_csv(self.csv_path)
        # Expect columns: temperature, humidity, rainfall, ph, label
        required = {"temperature", "humidity", "rainfall", "ph", "label"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Dataset missing columns: {missing}")

        X = df[["temperature", "humidity", "rainfall", "ph"]].astype(float)
        y = df["label"].astype(str)

        Xs = self.scaler.fit_transform(X)
        self.model = KNeighborsClassifier(n_neighbors=self.n_neighbors)
        self.model.fit(Xs, y)

    def predict(self, temperature: float, humidity: float, rainfall: float, ph: float) -> str:
        X = [[float(temperature), float(humidity), float(rainfall), float(ph)]]
        Xs = self.scaler.transform(X)
        return str(self.model.predict(Xs)[0])
