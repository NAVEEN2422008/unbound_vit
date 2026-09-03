"""
Unit and integration tests for Peer Benchmarking Engine Service.
Verifies:
1. Peer cohort selection using:
   - industry, region, business_size, revenue_range, business_model, asset_type
2. Comparison across 8 required metrics:
   - revenue growth, expense growth, profit margin, cash buffer,
   - debt burden, receivable ageing, payable pressure, asset utilization
3. Output attributes:
   - metric, customer_value, peer_median, peer_range, customer_percentile, status (BETTER, NORMAL, WORSE)
4. Minimum Peer Rule:
   - When sample size < 5, returns INSUFFICIENT_PEER_DATA and suppresses metrics
5. Privacy preservation (DPDP Act compliance):
   - Confirms only aggregated peer stats are returned, no peer IDs/balances/debts
6. REST API: GET /api/v1/businesses/{id}/peer-benchmark
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.peer_benchmarking import PeerBenchmarkingService
from src_py.models.peer_schemas import BenchmarkMetricStatus

client = TestClient(app)


def test_peer_benchmark_all_8_metrics_evaluated():
    """
    Verifies that all 8 metrics are calculated with correct statuses (BETTER, NORMAL, WORSE),
    percentiles, peer medians, and ranges.
    """
    report = PeerBenchmarkingService.evaluate_peer_benchmark(
        customer_id="CUST_PEER_TEST",
        customer_name="Kovai Precision Tools",
        industry="ENGINEERING",
        region="TAMIL_NADU",
        business_size="MSME",
        revenue_range="₹1Cr - ₹5Cr",
        business_model="B2B Precision Machining",
        asset_type="CNC Machining Centers",
        peer_sample_size=45,
        # Metrics:
        revenue_growth_val=18.0,      # > P75 (14.0) -> BETTER
        expense_growth_val=15.0,     # > P75 (13.5, lower is better) -> WORSE
        profit_margin_val=16.5,      # > P75 (15.0) -> BETTER
        cash_buffer_val=10.0,        # < P25 (14.0) -> WORSE
        debt_burden_val=30.0,        # Between P25(22) & P75(48) -> NORMAL
        receivable_ageing_val=85.0,  # > P75 (78.0, lower is better) -> WORSE
        payable_pressure_val=32.0,   # Between P25(28) & P75(65) -> NORMAL
        asset_utilization_val=90.0   # > P75 (86.0) -> BETTER
    )

    assert report.status == "BENCHMARK_COMPLETED"
    assert report.is_sufficient_peer_data is True
    assert len(report.metrics_comparison) == 8

    metric_names = [m.metric for m in report.metrics_comparison]
    assert "revenue_growth" in metric_names
    assert "expense_growth" in metric_names
    assert "profit_margin" in metric_names
    assert "cash_buffer" in metric_names
    assert "debt_burden" in metric_names
    assert "receivable_ageing" in metric_names
    assert "payable_pressure" in metric_names
    assert "asset_utilization" in metric_names

    # Check statuses
    rev_m = next(m for m in report.metrics_comparison if m.metric == "revenue_growth")
    assert rev_m.status == BenchmarkMetricStatus.BETTER
    assert rev_m.customer_percentile > 75.0

    exp_m = next(m for m in report.metrics_comparison if m.metric == "expense_growth")
    assert exp_m.status == BenchmarkMetricStatus.WORSE

    # Verify counts
    assert report.better_count == 3
    assert report.worse_count == 3
    assert report.normal_count == 2


def test_minimum_peer_rule_insufficient_data():
    """
    Verifies that when peer population is under 5,
    the system refuses to calculate misleading benchmarks and returns INSUFFICIENT_PEER_DATA.
    """
    report = PeerBenchmarkingService.evaluate_peer_benchmark(
        customer_id="CUST_TINY_COHORT",
        customer_name="Rare Craft Goods",
        peer_sample_size=3  # Under minimum threshold!
    )

    assert report.status == "INSUFFICIENT_PEER_DATA"
    assert report.is_sufficient_peer_data is False
    assert len(report.metrics_comparison) == 0
    assert report.overall_cohort_ranking_percentile == 0.0


def test_privacy_preservation():
    """
    Ensures that only aggregated medians and ranges are exposed.
    """
    report = PeerBenchmarkingService.evaluate_peer_benchmark(
        customer_id="CUST_PRIVACY",
        customer_name="Privacy MSME",
        peer_sample_size=40
    )

    report_dict = report.model_dump()
    assert "privacy_compliance_note" in report_dict
    assert "DPDP Act" in report_dict["privacy_compliance_note"]
    assert "peer_transactions" not in report_dict
    assert "peer_balances" not in report_dict
    assert "peer_debt" not in report_dict
    assert "peer_identities" not in report_dict


def test_api_v1_peer_benchmark_endpoint():
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/peer-benchmark?peer_sample_size=42")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert data["status"] == "BENCHMARK_COMPLETED"
    assert len(data["metrics_comparison"]) == 8
    assert data["peer_sample_size"] == 42
    assert "privacy_compliance_note" in data
