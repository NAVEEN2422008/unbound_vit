"""
Feature Store for FINRES.
Centralized feature computation, caching, and versioning for ML models.
Ensures training/serving consistency (avoiding training-serving skew).
"""
import hashlib
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import OrderedDict

from src_py.observability.logging import get_logger

logger = get_logger("finres.feature_store")

FEATURE_STORE_DIR = os.environ.get("FEATURE_STORE_DIR", "src_py/ai/feature_cache")
MAX_CACHE_SIZE = 1000


class FeatureStore:
    """
    In-memory LRU feature cache with file-backed persistence.
    Each feature set is versioned by input hash for idempotency.
    """

    def __init__(self, cache_dir: str = FEATURE_STORE_DIR):
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._cache_dir = cache_dir
        self._hit_count = 0
        self._miss_count = 0
        os.makedirs(cache_dir, exist_ok=True)
        self._load_persistent_cache()

    def _input_hash(self, customer_id: str, feature_version: str, input_data: Dict) -> str:
        raw = f"{customer_id}:{feature_version}:{json.dumps(input_data, sort_keys=True, default=str)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, customer_id: str, feature_version: str, input_data: Dict) -> Optional[Dict[str, Any]]:
        key = self._input_hash(customer_id, feature_version, input_data)
        if key in self._cache:
            self._hit_count += 1
            self._cache.move_to_end(key)
            return self._cache[key]
        self._miss_count += 1
        return None

    def put(self, customer_id: str, feature_version: str, input_data: Dict, features: Dict[str, Any]) -> None:
        key = self._input_hash(customer_id, feature_version, input_data)
        entry = {
            "customer_id": customer_id,
            "feature_version": feature_version,
            "features": features,
            "computed_at": datetime.utcnow().isoformat(),
        }
        self._cache[key] = entry
        self._cache.move_to_end(key)
        if len(self._cache) > MAX_CACHE_SIZE:
            self._cache.popitem(last=False)

    def get_or_compute(self, customer_id: str, feature_version: str, input_data: Dict, compute_fn) -> Dict[str, Any]:
        cached = self.get(customer_id, feature_version, input_data)
        if cached:
            logger.info(f"Feature cache HIT for {customer_id} v{feature_version}")
            return cached["features"]
        logger.info(f"Feature cache MISS for {customer_id} v{feature_version} — computing")
        features = compute_fn(input_data)
        self.put(customer_id, feature_version, input_data, features)
        return features

    def stats(self) -> Dict[str, Any]:
        total = self._hit_count + self._miss_count
        return {
            "cache_size": len(self._cache),
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": round(self._hit_count / total, 4) if total > 0 else 0.0,
            "max_capacity": MAX_CACHE_SIZE,
        }

    def invalidate(self, customer_id: Optional[str] = None) -> int:
        if customer_id is None:
            self._cache.clear()
            return 0
        keys = [k for k, v in self._cache.items() if v.get("customer_id") == customer_id]
        for k in keys:
            del self._cache[k]
        return len(keys)

    def _load_persistent_cache(self) -> None:
        for fname in os.listdir(self._cache_dir) if os.path.exists(self._cache_dir) else []:
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(self._cache_dir, fname)) as f:
                        entry = json.load(f)
                        key = fname.replace(".json", "")
                        self._cache[key] = entry
                except Exception as e:
                    logger.warning(f"Failed to load cache file {fname}: {e}")

    def persist(self) -> int:
        count = 0
        for key, entry in self._cache.items():
            path = os.path.join(self._cache_dir, f"{key}.json")
            try:
                with open(path, "w") as f:
                    json.dump(entry, f, default=str)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to persist cache entry {key}: {e}")
        return count


# Feature version registry
FEATURE_VERSIONS = {
    "base_v1": {
        "description": "9 base features: income, expense, debt service, cash, savings, EMI, receivables, payables, age",
        "version": "1.0.0",
    },
    "enriched_v1": {
        "description": "37 features: base + ratios, trends, seasonal patterns, interaction terms",
        "version": "1.0.0",
    },
    "v2": {
        "description": "42 features: enriched + SHAP attributions + drift indicators",
        "version": "2.0.0",
    },
}


def compute_base_features(income: float, expense: float, debt_service: float, cash: float,
                          savings: float, emi_total: float, receivables: float, payables: float,
                          age_months: int = 0) -> Dict[str, float]:
    """Compute 9 base features from raw financial inputs."""
    return {
        "income": income,
        "expense": expense,
        "debt_service": debt_service,
        "cash": cash,
        "savings": savings,
        "emi_total": emi_total,
        "receivables": receivables,
        "payables": payables,
        "age_months": age_months,
    }


def compute_enriched_features(base: Dict[str, float]) -> Dict[str, float]:
    """Compute 28 additional enriched features on top of base."""
    income = base["income"] or 1.0
    expense = base["expense"] or 1.0
    savings = base["savings"] or 0.0
    cash = base["cash"] or 0.0
    debt = base["debt_service"] or 0.0

    return {
        **base,
        "dsr": round(debt / income, 4) if income else 99.0,
        "expense_ratio": round(expense / income, 4) if income else 99.0,
        "savings_rate": round(savings / income, 4) if income else 0.0,
        "cash_buffer_days": round((cash / expense) * 30, 1) if expense else 999.0,
        "net_monthly": round(income - expense - debt, 2),
        "surplus_deficit": round(income - expense, 2),
        "debt_to_cash": round(debt / cash, 2) if cash else 99.0,
        "receivable_to_income": round(base["receivables"] / income, 2) if income else 0.0,
        "payable_to_income": round(base["payables"] / income, 2) if income else 0.0,
        "receivable_to_payable": round(base["receivables"] / base["payables"], 2) if base["payables"] else 99.0,
        "savings_to_cash": round(savings / cash, 2) if cash else 0.0,
        "income_log": round(__import__('math').log1p(income), 4),
        "expense_log": round(__import__('math').log1p(expense), 4),
        "cash_log": round(__import__('math').log1p(cash), 4),
        "is_income_zero": 1.0 if income < 1 else 0.0,
        "is_expense_gt_income": 1.0 if expense > income else 0.0,
        "is_dsr_high": 1.0 if debt / income > 0.6 else 0.0 if income else 1.0,
        "is_cash_low": 1.0 if cash < 50000 else 0.0,
        "is_negative_surplus": 1.0 if (income - expense - debt) < 0 else 0.0,
        "income_expense_ratio": round(income / expense, 2) if expense else 99.0,
        "emi_income_ratio": round(base["emi_total"] / income, 2) if income else 99.0,
        "cash_expense_ratio": round(cash / expense, 2) if expense else 999.0,
        "disposable_income": round(income - debt - expense, 2),
        "monthly_runway_months": round(cash / max(expense + debt, 1), 1),
        "receivable_gap_days": max(0, 30 - int(base.get("receivable_gap_days", 15))),
        "age_months": base.get("age_months", 0),
        "is_senior": 1.0 if base.get("age_months", 0) > 600 else 0.0,
    }


# Global singleton
_feature_store: Optional[FeatureStore] = None


def get_feature_store() -> FeatureStore:
    global _feature_store
    if _feature_store is None:
        _feature_store = FeatureStore()
    return _feature_store
