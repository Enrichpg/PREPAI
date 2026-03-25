"""Unit tests for the comfort ML model."""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch
import tempfile
import os




from app.services.ml.comfort_model import (
    compute_comfort_score_heuristic,
    engineer_features,
    ComfortModel,
    FEATURE_COLUMNS,
)


class TestComfortHeuristic:
    def _make_row(self, **kwargs):
        defaults = {
            "temperature": 15, "humidity": 65, "precipitation": 0,
            "precipitation_probability": 0, "wind_speed": 10, "wind_gust": 15,
            "cloud_cover": 40, "pressure": 1015, "uv_index": 3,
            "solar_radiation": 200, "fog": False, "visibility": 15,
        }
        defaults.update(kwargs)
        return pd.Series(defaults)

    def test_ideal_conditions_score_high(self):
        row = self._make_row(temperature=13, humidity=55, precipitation=0, wind_speed=8)
        score = compute_comfort_score_heuristic(row)
        assert score >= 85, f"Ideal conditions should score >= 85, got {score}"

    def test_heavy_rain_penalises(self):
        ideal = self._make_row()
        rainy = self._make_row(precipitation=15)
        assert compute_comfort_score_heuristic(rainy) < compute_comfort_score_heuristic(ideal) - 20

    def test_extreme_heat_penalises(self):
        row = self._make_row(temperature=38, uv_index=10)
        score = compute_comfort_score_heuristic(row)
        assert score < 40

    def test_freezing_penalises(self):
        row = self._make_row(temperature=-3)
        score = compute_comfort_score_heuristic(row)
        # -3°C → -40 penalty; ideal base 100 - 40 = 60; verify it's below ideal (85)
        ideal = compute_comfort_score_heuristic(self._make_row())
        assert score < ideal - 20

    def test_fog_penalises(self):
        normal = self._make_row()
        foggy = self._make_row(fog=True)
        assert compute_comfort_score_heuristic(foggy) < compute_comfort_score_heuristic(normal)

    def test_strong_wind_penalises(self):
        normal = self._make_row(wind_speed=10, wind_gust=15)
        windy = self._make_row(wind_speed=60, wind_gust=80)
        assert compute_comfort_score_heuristic(windy) < compute_comfort_score_heuristic(normal) - 15

    def test_score_bounded(self):
        rows = [
            self._make_row(temperature=50, precipitation=100, wind_speed=120),
            self._make_row(temperature=13, humidity=50),
        ]
        for row in rows:
            score = compute_comfort_score_heuristic(row)
            assert 0 <= score <= 100


class TestFeatureEngineering:
    def _make_df(self, n=5):
        return pd.DataFrame({
            "temperature": np.random.uniform(5, 25, n),
            "humidity": np.random.uniform(50, 90, n),
            "precipitation": np.zeros(n),
            "precipitation_probability": np.zeros(n),
            "wind_speed": np.random.uniform(5, 20, n),
            "wind_gust": np.random.uniform(10, 30, n),
            "cloud_cover": np.random.uniform(10, 80, n),
            "pressure": np.full(n, 1015.0),
            "uv_index": np.random.uniform(0, 6, n),
            "solar_radiation": np.random.uniform(50, 500, n),
            "fog": np.zeros(n),
            "hour": np.random.randint(6, 22, n),
            "month": np.random.randint(1, 13, n),
            "visibility": np.full(n, 15.0),
        })

    def test_all_feature_columns_present(self):
        df = self._make_df()
        engineered = engineer_features(df)
        for col in FEATURE_COLUMNS:
            assert col in engineered.columns, f"Missing feature: {col}"

    def test_cyclic_encoding_range(self):
        df = self._make_df()
        df["hour"] = [0, 6, 12, 18, 23]
        engineered = engineer_features(df)
        assert engineered["hour_sin"].between(-1, 1).all()
        assert engineered["hour_cos"].between(-1, 1).all()

    def test_no_nans_after_engineering(self):
        df = self._make_df()
        df.loc[0, "temperature"] = np.nan
        df.loc[1, "humidity"] = np.nan
        engineered = engineer_features(df)
        feature_df = engineered[FEATURE_COLUMNS]
        assert not feature_df.isnull().any().any(), "Feature columns should not contain NaN"


class TestComfortModel:
    def test_synthetic_training(self):
        model = ComfortModel()
        X, y = model._generate_synthetic_data()
        assert len(X) >= 1000
        assert len(y) == len(X)
        assert set(FEATURE_COLUMNS).issubset(set(X.columns))
        assert y.min() >= 0
        assert y.max() <= 100

    def test_train_and_predict(self):
        model = ComfortModel()
        X, y = model._generate_synthetic_data()
        X_small = X.head(500)
        y_small = y.head(500)

        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from xgboost import XGBRegressor

        X_train, X_val, y_train, y_val = train_test_split(X_small, y_small, test_size=0.2)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)

        m = XGBRegressor(n_estimators=50, n_jobs=1)
        m.fit(X_scaled, y_train)
        preds = m.predict(X_val_scaled)
        assert len(preds) == len(y_val)
        assert np.all(np.isfinite(preds))

    def test_heuristic_fallback(self):
        """Model should fall back to heuristic when no trained model exists."""
        model = ComfortModel()
        model.model = None
        model.scaler = None

        df = pd.DataFrame([{
            "temperature": 15, "humidity": 65, "precipitation": 0,
            "precipitation_probability": 0, "wind_speed": 10, "wind_gust": 15,
            "cloud_cover": 40, "pressure": 1015, "uv_index": 3,
            "solar_radiation": 200, "fog": 0.0, "hour": 8, "month": 5,
            "visibility": 15,
        }])
        scores = model.predict(df)
        assert len(scores) == 1
        assert 0 <= float(scores[0]) <= 100
