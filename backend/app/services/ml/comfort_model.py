"""
Running comfort score ML model.
Trains an XGBoost model to predict a 0-100 comfort score
based on meteorological variables.

Feature engineering reflects known running comfort factors:
- Temperature: ideal range 8-18°C
- Humidity: optimal 40-60%, high >80% penalised
- Rain: any rain reduces comfort significantly
- Wind: moderate (10-20 km/h) is OK, gusts >50 km/h dangerous
- Fog: visibility hazard
- UV: high UV penalises midday sessions
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from loguru import logger

from app.core.config import settings


FEATURE_COLUMNS = [
    "temperature",
    "humidity",
    "precipitation",
    "precipitation_probability",
    "wind_speed",
    "wind_gust",
    "cloud_cover",
    "pressure",
    "uv_index",
    "solar_radiation",
    "fog",
    "hour_sin",        # cyclic encoding of hour
    "hour_cos",
    "month_sin",       # cyclic encoding of month
    "month_cos",
    "temp_deviation",  # deviation from ideal temp (13°C)
    "humidity_penalty",
    "rain_penalty",
    "wind_penalty",
    "heat_index",      # apparent temperature
    "event_density",   # new feature: number of events in zone/hour
    "traffic_level",   # new feature: traffic congestion index
]

MODEL_VERSION_FILE = Path(settings.MODEL_PATH) / "model_version.json"
MODEL_FILE = Path(settings.MODEL_PATH) / "comfort_model.joblib"
SCALER_FILE = Path(settings.MODEL_PATH) / "comfort_scaler.joblib"
METRICS_FILE = Path(settings.MODEL_PATH) / "model_metrics.json"


def compute_comfort_score_heuristic(row: pd.Series) -> float:
    """
    Rule-based comfort score (0-100) used as training target
    when no labelled data exists. Based on sports science research.
    """
    score = 100.0

    # Temperature penalty (ideal: 8-18°C)
    temp = row.get("temperature", 15)
    if temp is None or pd.isna(temp):
        temp = 15
    if temp < 0:
        score -= 40
    elif temp < 5:
        score -= 20
    elif temp < 8:
        score -= 10
    elif 8 <= temp <= 18:
        score -= 0
    elif 18 < temp <= 22:
        score -= 5
    elif 22 < temp <= 28:
        score -= 15
    elif 28 < temp <= 33:
        score -= 30
    else:
        score -= 50

    # Humidity penalty
    humidity = row.get("humidity", 65) or 65
    if humidity > 90:
        score -= 20
    elif humidity > 80:
        score -= 10
    elif humidity > 70:
        score -= 5
    elif humidity < 30:
        score -= 5

    # Rain penalty
    prec = row.get("precipitation", 0) or 0
    prob_prec = row.get("precipitation_probability", 0) or 0
    if prec > 10:
        score -= 35
    elif prec > 5:
        score -= 25
    elif prec > 1:
        score -= 15
    elif prec > 0:
        score -= 10
    elif prob_prec > 70:
        score -= 10
    elif prob_prec > 50:
        score -= 5

    # Wind penalty
    wind = row.get("wind_speed", 0) or 0
    gust = row.get("wind_gust", 0) or 0
    if gust > 70 or wind > 50:
        score -= 35
    elif gust > 50 or wind > 35:
        score -= 20
    elif gust > 30 or wind > 25:
        score -= 10
    elif wind > 20:
        score -= 5

    # Fog penalty
    fog = row.get("fog", False)
    visibility = row.get("visibility")
    if fog or (visibility is not None and not pd.isna(visibility) and visibility < 0.5):
        score -= 20
    elif visibility is not None and not pd.isna(visibility) and visibility < 1:
        score -= 10

    # UV penalty (midday high UV)
    uv = row.get("uv_index", 0) or 0
    if uv >= 9:
        score -= 25
    elif uv >= 7:
        score -= 15
    elif uv >= 5:
        score -= 5

    # Cloud cover: mild clouds actually good (reduces heat/UV)
    cloud = row.get("cloud_cover", 50) or 50
    if cloud < 10:
        pass  # clear day, already penalized by UV if high
    elif 10 <= cloud <= 60:
        score += 2  # slight bonus
    elif cloud > 90:
        score -= 3

    return max(0.0, min(100.0, score))


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features to a weather dataframe."""
    df = df.copy()

    # Fill missing values with sensible defaults for A Coruña climate
    df["temperature"] = df["temperature"].fillna(14)
    df["humidity"] = df["humidity"].fillna(75)
    df["precipitation"] = df["precipitation"].fillna(0)
    df["precipitation_probability"] = df["precipitation_probability"].fillna(0)
    df["wind_speed"] = df["wind_speed"].fillna(15)
    df["wind_gust"] = df["wind_gust"].fillna(20)
    df["cloud_cover"] = df["cloud_cover"].fillna(50)
    df["pressure"] = df["pressure"].fillna(1015)
    df["uv_index"] = df["uv_index"].fillna(2)
    df["solar_radiation"] = df["solar_radiation"].fillna(100)
    df["fog"] = df["fog"].fillna(False).astype(float)

    # Cyclic encoding
    if "hour" in df.columns:
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    else:
        df["hour_sin"] = 0
        df["hour_cos"] = 1

    if "month" in df.columns:
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    else:
        df["month_sin"] = 0
        df["month_cos"] = 1

    # Deviation from ideal running temperature
    df["temp_deviation"] = (df["temperature"] - 13).abs()

    # Humidity discomfort (above 70%)
    df["humidity_penalty"] = (df["humidity"] - 70).clip(lower=0)

    # Rain penalty (log scale)
    df["rain_penalty"] = np.log1p(df["precipitation"])

    # Wind penalty
    df["wind_penalty"] = (df["wind_speed"] - 20).clip(lower=0)

    # Heat index (Steadman approximation)
    T = df["temperature"]
    H = df["humidity"]
    df["heat_index"] = -8.78469475556 + 1.61139411 * T + 2.33854883889 * H \
                       - 0.14611605 * T * H - 0.012308094 * T**2 \
                       - 0.0164248277778 * H**2 + 0.002211732 * T**2 * H \
                       + 0.00072546 * T * H**2 - 0.000003582 * T**2 * H**2

    return df


class ComfortModel:
    def __init__(self):
        self.model: Optional[XGBRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.version: Optional[str] = None
        self.metrics: Optional[Dict] = None
        self._ensure_dirs()

    def _ensure_dirs(self):
        Path(settings.MODEL_PATH).mkdir(parents=True, exist_ok=True)

    def _load_if_exists(self) -> bool:
        if MODEL_FILE.exists() and SCALER_FILE.exists():
            try:
                self.model = joblib.load(MODEL_FILE)
                self.scaler = joblib.load(SCALER_FILE)
                if MODEL_VERSION_FILE.exists():
                    with open(MODEL_VERSION_FILE) as f:
                        info = json.load(f)
                    self.version = info.get("version")
                    self.metrics = info.get("metrics")
                logger.info(f"Loaded comfort model v{self.version}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load existing model: {e}")
        return False

    def load(self) -> bool:
        return self._load_if_exists()

    def prepare_training_data(self, db_session) -> Tuple[pd.DataFrame, pd.Series]:
        # Pull weather observations from DB and generate training labels
        from sqlalchemy import text
        query = text("""
            SELECT
                wo.temperature,
                wo.humidity,
                wo.precipitation,
                wo.wind_speed,
                wo.wind_gust,
                wo.cloud_cover,
                wo.pressure,
                wo.uv_index,
                wo.solar_radiation,
                wo.fog,
                EXTRACT(HOUR FROM wo.observed_at) AS hour,
                EXTRACT(MONTH FROM wo.observed_at) AS month,
                0 AS precipitation_probability,
                wo.visibility
            FROM weather_observations wo
            WHERE wo.temperature IS NOT NULL
              AND wo.observed_at >= NOW() - INTERVAL '10 years'
            ORDER BY wo.observed_at DESC
            LIMIT 500000
        """)

        df = pd.read_sql(query.text if hasattr(query, 'text') else query, db_session.connection().connection)
        logger.info(f"Loaded {len(df)} observations for training")

        df = engineer_features(df)

        # Add event_density feature
        event_query = text("""
            SELECT zone_id, EXTRACT(HOUR FROM start_time) AS hour, COUNT(*) AS event_count
            FROM events
            WHERE start_time >= NOW() - INTERVAL '10 years'
            GROUP BY zone_id, hour
        """)
        event_df = pd.read_sql(event_query.text if hasattr(event_query, 'text') else event_query, db_session.connection().connection)
        event_density = []
        for idx, row in df.iterrows():
            hour = int(row["hour"]) if "hour" in row else 0
            match = event_df[(event_df["hour"] == hour)]
            density = match["event_count"].sum() if not match.empty else 0
            event_density.append(density)
        df["event_density"] = event_density

        # Add traffic_level feature
        traffic_query = text("""
            SELECT zone_id, EXTRACT(HOUR FROM timestamp) AS hour, AVG(traffic_level) AS avg_traffic
            FROM traffic_data
            WHERE timestamp >= NOW() - INTERVAL '10 years'
            GROUP BY zone_id, hour
        """)
        traffic_df = pd.read_sql(traffic_query.text if hasattr(traffic_query, 'text') else traffic_query, db_session.connection().connection)
        traffic_levels = []
        for idx, row in df.iterrows():
            hour = int(row["hour"]) if "hour" in row else 0
            match = traffic_df[(traffic_df["hour"] == hour)]
            level = match["avg_traffic"].mean() if not match.empty else 0
            traffic_levels.append(level)
        df["traffic_level"] = traffic_levels

        y = df.apply(compute_comfort_score_heuristic, axis=1)
        X = df[FEATURE_COLUMNS]
        return X, y

    def train(self, db_session) -> Dict:
        """Train or retrain the comfort model."""
        logger.info("Starting comfort model training...")
        X, y = self.prepare_training_data(db_session)

        if len(X) < 100:
            logger.warning("Insufficient training data — generating synthetic dataset")
            X, y = self._generate_synthetic_data()

        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42)

        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        self.model = XGBRegressor(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            early_stopping_rounds=20,
        )
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_val_scaled, y_val)],
            verbose=False,
        )

        y_pred = self.model.predict(X_val_scaled)
        mae = mean_absolute_error(y_val, y_pred)
        rmse = mean_squared_error(y_val, y_pred, squared=False)
        r2 = r2_score(y_val, y_pred)

        self.version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        feature_importances = dict(zip(FEATURE_COLUMNS, self.model.feature_importances_.tolist()))

        self.metrics = {
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "r2": round(r2, 4),
            "feature_importances": feature_importances,
            "training_samples": len(X_train),
            "validation_samples": len(X_val),
        }

        logger.info(f"Model trained — MAE={mae:.2f}, RMSE={rmse:.2f}, R2={r2:.4f}")

        # Save
        joblib.dump(self.model, MODEL_FILE)
        joblib.dump(self.scaler, SCALER_FILE)
        version_info = {
            "version": self.version,
            "trained_at": datetime.utcnow().isoformat(),
            "metrics": self.metrics,
        }
        with open(MODEL_VERSION_FILE, "w") as f:
            json.dump(version_info, f, indent=2)
        with open(METRICS_FILE, "w") as f:
            json.dump(version_info, f, indent=2)

        return self.metrics

    def _generate_synthetic_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Generate synthetic training data based on known comfort heuristics."""
        np.random.seed(42)
        n = 50000
        rows = []
        for _ in range(n):
            temp = np.random.uniform(-5, 40)
            humidity = np.random.uniform(20, 100)
            prec = np.random.exponential(0.5) * np.random.choice([0, 0, 0, 1])
            wind = np.array(np.random.exponential(15)).clip(0, 100)
            gust = wind * np.random.uniform(1, 2)
            cloud = np.random.uniform(0, 100)
            pressure = np.random.normal(1015, 10)
            uv = np.random.uniform(0, 11)
            radiation = np.random.uniform(0, 1000)
            fog = np.random.random() < 0.05
            hour = np.random.randint(0, 24)
            month = np.random.randint(1, 13)
            visibility = np.random.uniform(0.2, 30)
            rows.append({
                "temperature": temp, "humidity": humidity,
                "precipitation": prec, "precipitation_probability": prec * 20,
                "wind_speed": wind, "wind_gust": gust,
                "cloud_cover": cloud, "pressure": pressure,
                "uv_index": uv, "solar_radiation": radiation,
                "fog": fog, "hour": hour, "month": month,
                "visibility": visibility,
                "event_density": np.random.randint(0, 10),
                "traffic_level": np.random.uniform(0, 1),
            })
        df = pd.DataFrame(rows)
        df = engineer_features(df)
        y = df.apply(compute_comfort_score_heuristic, axis=1)
        return df[FEATURE_COLUMNS], y

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Predict comfort scores for a batch of feature rows."""
        if self.model is None or self.scaler is None:
            if not self.load():
                logger.warning("No trained model found, using heuristic fallback")
                return features.apply(compute_comfort_score_heuristic, axis=1).values

        features_engineered = engineer_features(features)
        X = features_engineered[FEATURE_COLUMNS]
        X_scaled = self.scaler.transform(X)
        scores = self.model.predict(X_scaled)
        return np.clip(scores, 0, 100)

    def predict_single(self, weather: Dict) -> float:
        df = pd.DataFrame([weather])
        return float(self.predict(df)[0])

    def get_metrics(self) -> Optional[Dict]:
        if self.metrics:
            return self.metrics
        if METRICS_FILE.exists():
            with open(METRICS_FILE) as f:
                data = json.load(f)
            self.metrics = data.get("metrics")
            self.version = data.get("version")
            return self.metrics
        return None


# Singleton instance
_model_instance: Optional[ComfortModel] = None


def get_comfort_model() -> ComfortModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = ComfortModel()
        _model_instance.load()
    return _model_instance
