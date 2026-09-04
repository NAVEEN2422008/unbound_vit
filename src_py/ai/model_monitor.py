"""
Model Monitoring & Drift Detection for FINRES ML Models.
Tracks prediction distributions, detects data drift, monitors model performance decay.
"""
import json
import os
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np

from src_py.observability.logging import get_logger

logger = get_logger("finres.model_monitor")

MONITOR_DIR = os.environ.get("MONITOR_DIR", "src_py/ai/monitor_data")


@dataclass
class DriftAlert:
    model_name: str
    metric: str
    current_value: float
    baseline_value: float
    drift_magnitude: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class ModelPerformanceSnapshot:
    model_name: str
    accuracy: float
    auc: float
    precision: float
    recall: float
    f1: float
    total_predictions: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ModelMonitor:
    """
    Production model monitoring with:
    - Prediction distribution tracking (scores, latencies)
    - Data drift detection via PSI (Population Stability Index)
    - Model performance decay alerts
    - Hallucination / anomalous prediction detection
    """

    def __init__(self, window_size: int = 1000):
        self._window_size = window_size
        self._prediction_scores: Dict[str, deque] = {}
        self._prediction_latencies: Dict[str, deque] = {}
        self._baseline_distributions: Dict[str, Dict[str, float]] = {}
        self._drift_alerts: List[DriftAlert] = []
        self._performance_history: List[ModelPerformanceSnapshot] = []
        self._anomaly_count = 0
        self._total_predictions = 0
        os.makedirs(MONITOR_DIR, exist_ok=True)
        self._load_baselines()

    def record_prediction(self, model_name: str, score: float, latency_ms: float) -> None:
        if model_name not in self._prediction_scores:
            self._prediction_scores[model_name] = deque(maxlen=self._window_size)
            self._prediction_latencies[model_name] = deque(maxlen=self._window_size)

        self._prediction_scores[model_name].append(score)
        self._prediction_latencies[model_name].append(latency_ms)
        self._total_predictions += 1

        if score < 0 or score > 1:
            self._anomaly_count += 1
            logger.warning(f"Anomalous prediction score {score} from {model_name}")

    def check_drift(self, model_name: str) -> Optional[DriftAlert]:
        if model_name not in self._baseline_distributions:
            return None
        if model_name not in self._prediction_scores:
            return None
        if len(self._prediction_scores[model_name]) < 50:
            return None

        baseline = self._baseline_distributions[model_name]
        current_scores = list(self._prediction_scores[model_name])
        current_mean = np.mean(current_scores)
        current_std = np.std(current_scores)

        psi = self._compute_psi(
            baseline.get("bins", [0, 0.25, 0.5, 0.75, 1.0]),
            baseline.get("counts", [0.25, 0.25, 0.25, 0.25]),
            self._histogram_counts(current_scores)
        )

        severity = "LOW"
        if psi > 0.25:
            severity = "CRITICAL"
        elif psi > 0.1:
            severity = "HIGH"
        elif psi > 0.05:
            severity = "MEDIUM"

        if psi > 0.05:
            alert = DriftAlert(
                model_name=model_name,
                metric="PSI",
                current_value=round(psi, 4),
                baseline_value=baseline.get("psi_baseline", 0.0),
                drift_magnitude=round(psi, 4),
                severity=severity,
            )
            self._drift_alerts.append(alert)
            logger.warning(f"Drift detected for {model_name}: PSI={psi:.4f} ({severity})")
            return alert
        return None

    def record_performance(self, snapshot: ModelPerformanceSnapshot) -> None:
        self._performance_history.append(snapshot)
        if len(self._performance_history) > 500:
            self._performance_history = self._performance_history[-500:]

    def get_health(self) -> Dict[str, Any]:
        models_status = {}
        for name, scores in self._prediction_scores.items():
            latencies = self._prediction_latencies.get(name, deque())
            models_status[name] = {
                "predictions_count": len(scores),
                "score_mean": round(float(np.mean(scores)), 4) if scores else 0,
                "score_std": round(float(np.std(scores)), 4) if scores else 0,
                "avg_latency_ms": round(float(np.mean(latencies)), 2) if latencies else 0,
                "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2) if latencies else 0,
            }

        return {
            "total_predictions": self._total_predictions,
            "anomaly_count": self._anomaly_count,
            "active_alerts": len([a for a in self._drift_alerts if a.severity in ("HIGH", "CRITICAL")]),
            "models": models_status,
            "recent_alerts": [
                {
                    "model": a.model_name,
                    "metric": a.metric,
                    "severity": a.severity,
                    "value": a.current_value,
                    "at": a.detected_at,
                }
                for a in self._drift_alerts[-10:]
            ],
        }

    def set_baseline(self, model_name: str, scores: List[float]) -> None:
        bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        counts = self._histogram_counts(scores, bins)
        total = sum(counts)
        proportions = [c / total if total else 1 / len(counts) for c in counts]
        self._baseline_distributions[model_name] = {
            "bins": bins,
            "counts": proportions,
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "psi_baseline": 0.0,
            "set_at": datetime.utcnow().isoformat(),
        }

    def _compute_psi(self, bins: List[float], baseline_counts: List[float], current_counts: List[float]) -> float:
        psi = 0.0
        eps = 1e-6
        for b, c in zip(baseline_counts, current_counts):
            b = max(b, eps)
            c = max(c, eps)
            psi += (c - b) * np.log(c / b)
        return float(psi)

    def _histogram_counts(self, scores: List[float], bins: Optional[List[float]] = None) -> List[float]:
        if bins is None:
            bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        counts = [0.0] * (len(bins) - 1)
        for s in scores:
            for i in range(len(bins) - 1):
                if bins[i] <= s < bins[i + 1]:
                    counts[i] += 1
                    break
            else:
                if s >= bins[-1]:
                    counts[-1] += 1
        total = sum(counts)
        return [c / total if total else 1 / len(counts) for c in counts]

    def _load_baselines(self) -> None:
        path = os.path.join(MONITOR_DIR, "baselines.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self._baseline_distributions = json.load(f)
            except Exception:
                pass

    def persist(self) -> None:
        path = os.path.join(MONITOR_DIR, "baselines.json")
        with open(path, "w") as f:
            json.dump(self._baseline_distributions, f, default=str)


# Global singleton
_monitor: Optional[ModelMonitor] = None


def get_model_monitor() -> ModelMonitor:
    global _monitor
    if _monitor is None:
        _monitor = ModelMonitor()
    return _monitor
