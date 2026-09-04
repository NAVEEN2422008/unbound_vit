"""
Model Registry for FINRES ML.
Loads saved models and serves predictions.
"""
import os
import json
import numpy as np
import joblib
from typing import Dict, Optional, List, Tuple

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "model_artifacts")


class ModelRegistry:
    """Loads and manages trained models for prediction serving."""

    _instance = None
    _loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._loaded:
            self._models = {}
            self._scalers = {}
            self._registry = {}
            self._feature_config = {}
            self._load_all()
            self.__class__._loaded = True

    def _load_all(self):
        """Load all model artifacts from disk."""
        registry_path = os.path.join(ARTIFACTS_DIR, "model_registry.json")
        if not os.path.exists(registry_path):
            print("[ModelRegistry] No trained models found. Run trainer.py first.")
            return

        with open(registry_path) as f:
            self._registry = json.load(f)

        feature_config_path = os.path.join(ARTIFACTS_DIR, "feature_config.json")
        if os.path.exists(feature_config_path):
            with open(feature_config_path) as f:
                self._feature_config = json.load(f)

        for name in self._registry:
            model_path = os.path.join(ARTIFACTS_DIR, f"{name}.joblib")
            if os.path.exists(model_path):
                self._models[name] = joblib.load(model_path)

        scaler_base_path = os.path.join(ARTIFACTS_DIR, "scaler_base.joblib")
        if os.path.exists(scaler_base_path):
            self._scalers["base"] = joblib.load(scaler_base_path)

        scaler_enriched_path = os.path.join(ARTIFACTS_DIR, "scaler_enriched.joblib")
        if os.path.exists(scaler_enriched_path):
            self._scalers["enriched"] = joblib.load(scaler_enriched_path)

        print(f"[ModelRegistry] Loaded {len(self._models)} models: {list(self._models.keys())}")

    def get_model(self, name: str):
        return self._models.get(name)

    def get_scaler(self, name: str):
        return self._scalers.get(name)

    def get_best_model_name(self) -> Optional[str]:
        if not self._registry:
            return None
        return max(self._registry.keys(), key=lambda k: self._registry[k].get("auc", 0))

    def get_model_info(self, name: str) -> Optional[Dict]:
        return self._registry.get(name)

    def list_models(self) -> List[Dict]:
        return [{"name": k, **v} for k, v in self._registry.items()]

    def predict_distress(self, features: np.ndarray, model_name: Optional[str] = None) -> Dict:
        """Predict distress probability using the specified or best model."""
        if not self._models:
            return {"error": "No models loaded", "score": 50, "probability": 0.5, "confidence": 0.3}

        X = features.reshape(1, -1) if features.ndim == 1 else features
        if model_name is None:
            if X.shape[1] <= 9:
                model_name = "distress_random_forest" if "distress_random_forest" in self._models else "distress_logistic"
            else:
                model_name = self.get_best_model_name()

        model = self._models.get(model_name)
        if model is None:
            return {"error": f"Model '{model_name}' not found", "score": 50, "probability": 0.5}

        scaler = None
        model_info = self._registry.get(model_name, {})
        n_features = model_info.get("n_features", 9)

        if n_features <= 9:
            scaler = self._scalers.get("base")
        else:
            scaler = self._scalers.get("enriched")

        X = features.reshape(1, -1) if features.ndim == 1 else features

        if X.shape[1] < n_features:
            padding = np.zeros((X.shape[0], n_features - X.shape[1]))
            X = np.hstack([X, padding])
        elif X.shape[1] > n_features:
            X = X[:, :n_features]

        if scaler is not None and hasattr(model, "coef_"):
            X = scaler.transform(X)

        proba = model.predict_proba(X)[0]
        distress_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
        distress_score = int(round(distress_prob * 100))
        distress_score = max(0, min(100, distress_score))

        if distress_prob > 0.7:
            risk_level = "CRITICAL"
        elif distress_prob > 0.5:
            risk_level = "HIGH"
        elif distress_prob > 0.3:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        feature_importance = model_info.get("feature_importance", {})
        top_factors = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "score": distress_score,
            "probability": round(distress_prob, 4),
            "risk_level": risk_level,
            "model_used": model_name,
            "model_auc": model_info.get("auc", 0),
            "top_risk_factors": [{"feature": f, "importance": imp} for f, imp in top_factors],
            "confidence": round(float(model_info.get("cv_auc_mean", 0.5)), 3),
        }


_registry = None


def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def predict_distress(features: np.ndarray, model_name: Optional[str] = None) -> Dict:
    return get_registry().predict_distress(features, model_name)


def get_all_models() -> List[Dict]:
    return get_registry().list_models()


def get_model_info(name: str) -> Optional[Dict]:
    return get_registry().get_model_info(name)
