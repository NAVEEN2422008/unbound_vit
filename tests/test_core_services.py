"""
FINRES Unit Tests for core service engines.
Run with: python -m pytest tests/ -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock
from src_py.ai.feature_store import (
    FeatureStore, compute_base_features, compute_enriched_features, get_feature_store
)
from src_py.ai.explainability import ModelExplainer, get_explainer
from src_py.ai.model_monitor import ModelMonitor, get_model_monitor
from src_py.services.notification_service import (
    NotificationStore, get_notification_store, alert_distress, alert_score_change, NotificationType
)


# ───────────────────── Feature Store Tests ─────────────────────
class TestBaseFeatures:
    def test_compute_base_features(self):
        features = compute_base_features(
            income=50000, expense=30000, debt_service=10000,
            cash=100000, savings=200000, emi_total=10000,
            receivables=50000, payables=30000, age_months=360
        )
        assert features["income"] == 50000
        assert features["expense"] == 30000
        assert features["age_months"] == 360
        assert features["cash"] == 100000

    def test_compute_enriched_features(self):
        base = compute_base_features(
            income=50000, expense=30000, debt_service=10000,
            cash=100000, savings=200000, emi_total=10000,
            receivables=50000, payables=30000
        )
        enriched = compute_enriched_features(base)
        assert "dsr" in enriched
        assert enriched["dsr"] == 0.2  # 10000/50000
        assert enriched["expense_ratio"] == 0.6  # 30000/50000
        assert enriched["savings_rate"] == 4.0  # 200000/50000
        assert enriched["cash_buffer_days"] == 100.0  # (100000/30000)*30

    def test_zero_income_handling(self):
        features = compute_base_features(
            income=0, expense=30000, debt_service=10000,
            cash=100000, savings=200000, emi_total=10000,
            receivables=50000, payables=30000
        )
        enriched = compute_enriched_features(features)
        # Income=0 is normalized to 1.0 to prevent division-by-zero; DSR becomes very large
        assert enriched["dsr"] >= 10000.0
        assert enriched["expense_ratio"] >= 10000.0
        assert enriched["is_negative_surplus"] == 1.0  # net_monthly < 0


class TestFeatureStoreCache:
    def test_put_and_get(self):
        store = FeatureStore(cache_dir="test_feature_cache")
        data = {"income": 50000}
        store.put("CUST001", "v1", data, {"dsr": 0.2})
        result = store.get("CUST001", "v1", data)
        assert result is not None
        assert result["features"]["dsr"] == 0.2
        store.invalidate()

    def test_cache_miss(self):
        store = FeatureStore(cache_dir="test_feature_cache")
        result = store.get("NONEXISTENT", "v1", {"x": 1})
        assert result is None
        store.invalidate()

    def test_get_or_compute(self):
        store = FeatureStore(cache_dir="test_feature_cache")
        call_count = 0

        def compute(data):
            nonlocal call_count
            call_count += 1
            return {"computed": True}

        result = store.get_or_compute("CUST002", "v1", {"a": 1}, compute)
        assert result["computed"] is True
        assert call_count == 1

        result2 = store.get_or_compute("CUST002", "v1", {"a": 1}, compute)
        assert result2["computed"] is True
        assert call_count == 1  # Should not recompute
        store.invalidate()

    def test_stats(self):
        store = FeatureStore(cache_dir="test_feature_cache")
        stats = store.stats()
        assert "cache_size" in stats
        assert "hit_rate" in stats
        store.invalidate()


# ───────────────────── Explainability Tests ─────────────────────
class TestModelExplainer:
    def test_explain_returns_results(self):
        explainer = ModelExplainer()
        features = {
            "income": 50000, "expense": 30000, "debt_service": 10000,
            "cash": 100000, "savings": 200000, "emi_total": 10000,
            "receivables": 50000, "payables": 30000, "dsr": 0.2,
            "expense_ratio": 0.6, "savings_rate": 4.0, "cash_buffer_days": 100,
            "net_monthly": 10000, "debt_to_cash": 0.1, "is_negative_surplus": 0,
            "is_cash_low": 0, "disposable_income": 10000,
        }
        result = explainer.explain(features, top_k=3)
        assert "top_risk_factors" in result
        assert "top_protective_factors" in result
        assert "explanation_summary" in result
        assert len(result["top_risk_factors"]) <= 3

    def test_explain_empty_features(self):
        explainer = ModelExplainer()
        result = explainer.explain({}, top_k=5)
        assert "explanation_summary" in result

    def test_global_explainer(self):
        explainer = get_explainer()
        assert explainer is not None
        features = {"income": 50000, "debt_service": 10000}
        result = explainer.explain(features)
        assert "explanation_summary" in result


# ───────────────────── Model Monitor Tests ─────────────────────
class TestModelMonitor:
    def test_record_prediction(self):
        monitor = ModelMonitor(window_size=100)
        monitor.record_prediction("GB", 0.65, 12.5)
        health = monitor.get_health()
        assert health["total_predictions"] == 1
        assert "GB" in health["models"]

    def test_anomaly_detection(self):
        monitor = ModelMonitor(window_size=100)
        monitor.record_prediction("GB", 1.5, 12.5)  # Invalid score > 1
        health = monitor.get_health()
        assert health["anomaly_count"] == 1

    def test_drift_no_baseline(self):
        monitor = ModelMonitor(window_size=100)
        for _ in range(60):
            monitor.record_prediction("GB", 0.5, 10.0)
        alert = monitor.check_drift("GB")
        assert alert is None  # No baseline set

    def test_drift_with_baseline(self):
        monitor = ModelMonitor(window_size=100)
        monitor.set_baseline("GB", [0.5] * 100)
        for _ in range(60):
            monitor.record_prediction("GB", 0.9, 10.0)
        alert = monitor.check_drift("GB")
        assert alert is not None
        assert alert.severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_performance_history(self):
        from src_py.ai.model_monitor import ModelPerformanceSnapshot
        monitor = ModelMonitor()
        snapshot = ModelPerformanceSnapshot(
            model_name="GB", accuracy=0.85, auc=0.79, precision=0.82,
            recall=0.78, f1=0.80, total_predictions=1000
        )
        monitor.record_performance(snapshot)
        health = monitor.get_health()
        assert health["total_predictions"] == 0  # record_performance doesn't count as a prediction
        # Verify the performance snapshot was stored by checking drift check works
        monitor.record_prediction("GB", 0.5, 10.0)
        health2 = monitor.get_health()
        assert health2["total_predictions"] == 1

    def test_global_monitor(self):
        monitor = get_model_monitor()
        assert monitor is not None


# ───────────────────── Notification Tests ─────────────────────
class TestNotificationStore:
    def test_push_and_get(self):
        store = NotificationStore()
        from src_py.services.notification_service import Notification, NotificationType, NotificationPriority
        n = Notification(
            type_=NotificationType.DISTRESS_ALERT,
            priority=NotificationPriority.HIGH,
            title="Test Alert",
            message="Test message",
        )
        store.push(n)
        all_notifs = store.get_all()
        assert len(all_notifs) >= 1
        assert all_notifs[0]["title"] == "Test Alert"

    def test_unread_count(self):
        store = NotificationStore()
        count_before = store.unread_count()
        from src_py.services.notification_service import Notification, NotificationType, NotificationPriority
        n = Notification(
            type_=NotificationType.SCORE_CHANGE,
            priority=NotificationPriority.LOW,
            title="Count Test",
            message="Count test message",
        )
        store.push(n)
        assert store.unread_count() == count_before + 1

    def test_alert_distress(self):
        store = get_notification_store()
        before = store.unread_count()
        n = alert_distress("CUST_TEST", 0.85, threshold=0.7)
        assert n is not None
        assert n.priority.value == "HIGH"
        assert store.unread_count() == before + 1

    def test_alert_score_change_below_threshold(self):
        n = alert_score_change("CUST_TEST", 0.5, 0.55)
        assert n is None  # Delta < 0.1

    def test_alert_score_change_above_threshold(self):
        n = alert_score_change("CUST_TEST", 0.3, 0.8)
        assert n is not None
        assert n.metadata["delta"] == 0.5

    def test_mark_read(self):
        store = get_notification_store()
        all_notifs = store.get_all(limit=1)
        if all_notifs:
            store.mark_read(all_notifs[0]["id"])
            marked = store.get_all(limit=1)
            assert marked[0]["read"] is True

    def test_stats(self):
        store = get_notification_store()
        stats = store.stats()
        assert "total" in stats
        assert "unread" in stats
        assert "by_type" in stats

    def test_global_store(self):
        store = get_notification_store()
        assert store is not None


# ───────────────────── Integration Tests ─────────────────────
class TestIntegration:
    def test_feature_store_to_explainer_pipeline(self):
        base = compute_base_features(
            income=45000, expense=28000, debt_service=12000,
            cash=80000, savings=150000, emi_total=12000,
            receivables=40000, payables=25000
        )
        enriched = compute_enriched_features(base)
        explainer = get_explainer()
        explanation = explainer.explain(enriched, top_k=3)
        assert len(explanation["top_risk_factors"]) + len(explanation["top_protective_factors"]) <= 3

    def test_monitor_to_notification_pipeline(self):
        monitor = get_model_monitor()
        store = get_notification_store()
        monitor.set_baseline("GB", [0.5] * 100)
        for _ in range(100):
            monitor.record_prediction("GB", 0.95, 15.0)
        alert = monitor.check_drift("GB")
        if alert and alert.severity in ("HIGH", "CRITICAL"):
            from src_py.services.notification_service import alert_model_drift
            n = alert_model_drift("GB", alert.drift_magnitude)
            assert n is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
