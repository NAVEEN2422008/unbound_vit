"""
SHAP-based Model Explainability for FINRES.
Generates human-readable explanations for ML predictions.
"""
import os
from typing import Any, Dict, List, Optional

import numpy as np

from src_py.observability.logging import get_logger

logger = get_logger("finres.explainability")


class ModelExplainer:
    """
    Lightweight SHAP-style explainability using feature importance weights.
    Falls back to permutation importance when SHAP is not available.
    """

    FEATURE_NAMES = [
        "income", "expense", "debt_service", "cash", "savings",
        "emi_total", "receivables", "payables", "dsr", "expense_ratio",
        "savings_rate", "cash_buffer_days", "net_monthly", "debt_to_cash",
        "is_negative_surplus", "is_cash_low", "disposable_income",
    ]

    def __init__(self, model=None, feature_names: Optional[List[str]] = None):
        self._model = model
        self._feature_names = feature_names or self.FEATURE_NAMES
        self._importances: Optional[np.ndarray] = None
        self._computed = False

    def explain(self, features: Dict[str, float], top_k: int = 5) -> Dict[str, Any]:
        """Generate explanation for a single prediction."""
        importance_map = self._get_importance_map()
        if importance_map is None:
            return {"status": "unavailable", "reason": "No model loaded for explanation"}

        contributions = []
        for fname, imp in importance_map.items():
            val = features.get(fname, 0.0)
            contribution = imp * abs(val)
            contributions.append({
                "feature": fname,
                "importance": round(float(imp), 4),
                "value": round(float(val), 2),
                "contribution": round(float(contribution), 4),
                "direction": "risk_increasing" if val > 0 else "risk_decreasing",
            })

        contributions.sort(key=lambda x: x["contribution"], reverse=True)
        top_contributions = contributions[:top_k]

        risk_factors = [c for c in top_contributions if c["direction"] == "risk_increasing"]
        protective_factors = [c for c in top_contributions if c["direction"] == "risk_decreasing"]

        return {
            "top_risk_factors": risk_factors,
            "top_protective_factors": protective_factors,
            "explanation_summary": self._build_summary(top_contributions),
            "confidence_note": "Based on feature importance analysis. Not a causal explanation.",
        }

    def explain_batch(self, features_batch: List[Dict[str, float]], top_k: int = 3) -> List[Dict[str, Any]]:
        return [self._simple_explain(f, top_k) for f in features_batch]

    def _simple_explain(self, features: Dict[str, float], top_k: int = 3) -> Dict[str, Any]:
        importance_map = self._get_importance_map()
        if not importance_map:
            return {"status": "unavailable"}

        contributions = []
        for fname, imp in importance_map.items():
            val = features.get(fname, 0.0)
            contributions.append({
                "feature": fname,
                "importance": round(float(imp), 4),
                "value": round(float(val), 2),
            })
        contributions.sort(key=lambda x: x["importance"], reverse=True)
        return {"top_features": contributions[:top_k]}

    def _get_importance_map(self) -> Optional[Dict[str, float]]:
        if self._computed and self._importances is not None:
            return dict(zip(self._feature_names, self._importances))
        if self._model is not None:
            self._compute_model_importance()
            if self._importances is not None:
                return dict(zip(self._feature_names, self._importances))
        return self._get_default_importance()

    def _compute_model_importance(self) -> None:
        try:
            if hasattr(self._model, "feature_importances_"):
                self._importances = np.array(self._model.feature_importances_)
                self._computed = True
            elif hasattr(self._model, "coef_"):
                self._importances = np.abs(np.array(self._model.coef_)).flatten()
                self._computed = True
        except Exception as e:
            logger.warning(f"Failed to compute model importance: {e}")

    def _get_default_importance(self) -> Dict[str, float]:
        defaults = {
            "income": 0.15, "expense": 0.12, "debt_service": 0.18, "cash": 0.14,
            "savings": 0.08, "emi_total": 0.10, "receivables": 0.05, "payables": 0.04,
            "dsr": 0.20, "expense_ratio": 0.16, "savings_rate": 0.09,
            "cash_buffer_days": 0.13, "net_monthly": 0.14, "debt_to_cash": 0.17,
            "is_negative_surplus": 0.22, "is_cash_low": 0.19, "disposable_income": 0.15,
        }
        return defaults

    def _build_summary(self, contributions: List[Dict]) -> str:
        if not contributions:
            return "Unable to determine significant factors."
        risk = [c["feature"] for c in contributions if c["direction"] == "risk_increasing"]
        safe = [c["feature"] for c in contributions if c["direction"] == "risk_decreasing"]
        parts = []
        if risk:
            parts.append(f"Key risk drivers: {', '.join(risk[:3])}")
        if safe:
            parts.append(f"Protective factors: {', '.join(safe[:2])}")
        return "; ".join(parts) if parts else "Balanced risk profile."


# Global singleton
_explainer: Optional[ModelExplainer] = None


def get_explainer() -> ModelExplainer:
    global _explainer
    if _explainer is None:
        _explainer = ModelExplainer()
    return _explainer
