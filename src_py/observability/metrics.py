"""
Prometheus-compatible Metrics for FINRES.
Exposes counters, histograms, and gauges for model monitoring, latency, and throughput.
"""
import time
from collections import defaultdict
from typing import Dict, List


class MetricsCollector:
    """In-process metrics collector. Replace with prometheus_client in production."""

    def __init__(self):
        self._counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._gauges: Dict[str, float] = {}

    def inc(self, name: str, labels: Dict[str, str] = None, amount: int = 1) -> None:
        key = self._key(name, labels)
        self._counters[name][key] += amount

    def observe(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        key = self._key(name, labels)
        self._histograms[name].append(value)
        # Keep last 1000 samples for percentile calc
        if len(self._histograms[name]) > 1000:
            self._histograms[name] = self._histograms[name][-1000:]

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        key = self._key(name, labels)
        self._gauges[key] = value

    def _key(self, name: str, labels: Dict[str, str] = None) -> str:
        if not labels:
            return name
        parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return f"{name}{{{','.join(parts)}}}"

    def get_summary(self) -> Dict:
        """Return a snapshot of all metrics."""
        return {
            "counters": {k: dict(v) for k, v in self._counters.items()},
            "histograms": {k: self._histogram_stats(v) for k, v in self._histograms.items()},
            "gauges": dict(self._gauges),
        }

    def _histogram_stats(self, values: List[float]) -> Dict:
        if not values:
            return {"count": 0}
        s = sorted(values)
        n = len(s)
        return {
            "count": n,
            "p50": s[n // 2],
            "p95": s[int(n * 0.95)] if n > 20 else s[-1],
            "p99": s[int(n * 0.99)] if n > 100 else s[-1],
            "mean": sum(s) / n,
            "max": s[-1],
        }

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        for name, entries in self._counters.items():
            for key, val in entries.items():
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{key} {val}")
        for name, entries in self._gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {entries}")
        for name, stats in self.get_summary()["histograms"].items():
            lines.append(f"# TYPE {name} summary")
            lines.append(f"{name}_count {stats.get('count', 0)}")
            for p in ("p50", "p95", "p99"):
                if p in stats:
                    lines.append(f"{name}{{quantile=\"{p}\"}} {stats[p]}")
        return "\n".join(lines)


metrics = MetricsCollector()


# Pre-defined metric names
METRIC_REQUEST_COUNT = "finres_http_requests_total"
METRIC_REQUEST_DURATION = "finres_http_request_duration_seconds"
METRIC_DISTRESS_PREDICTION = "finres_distress_predictions_total"
METRIC_MODEL_INFERENCE = "finres_model_inference_seconds"
METRIC_DB_QUERY = "finres_db_queries_total"
METRIC_ACTIVE_CUSTOMERS = "finres_active_customers"
METRIC_MODEL_ACCURACY = "finres_model_accuracy"


def record_prediction(model_name: str, score: float, duration_ms: float) -> None:
    metrics.inc(METRIC_DISTRESS_PREDICTION, {"model": model_name})
    metrics.observe(METRIC_MODEL_INFERENCE, duration_ms / 1000, {"model": model_name})


def record_request(method: str, path: str, status_code: int, duration_ms: float) -> None:
    metrics.inc(METRIC_REQUEST_COUNT, {"method": method, "path": path, "status": str(status_code)})
    metrics.observe(METRIC_REQUEST_DURATION, duration_ms / 1000, {"method": method, "path": path})


def set_active_customers(count: int) -> None:
    metrics.set_gauge(METRIC_ACTIVE_CUSTOMERS, count)


def set_model_accuracy(model_name: str, accuracy: float) -> None:
    metrics.set_gauge(METRIC_MODEL_ACCURACY, {"model": model_name}, accuracy)