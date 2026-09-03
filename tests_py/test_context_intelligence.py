"""
Unit and acceptance tests for Context-Aware Distress Intelligence Service.
Verifies:
1. 6-Step context evaluation process:
   - customer growth, industry median, regional median, peer-group median, seasonal baseline, deviations
2. Acceptance Criteria:
   - Correctly distinguishes customer downturn + industry downturn (NORMAL_SEASONAL / INDUSTRY_WIDE)
   - from customer downturn + stable industry (CUSTOMER_SPECIFIC)
3. Specification Example 1:
   - Customer: -20%, Industry: -18%, Region: -17%, Peers: -19% -> NORMAL_SEASONAL / INDUSTRY_WIDE
4. Specification Example 2:
   - Customer: -35%, Industry: -7%, Region: -9%, Peers: -8% -> CUSTOMER_SPECIFIC
5. Minimum Peer Rule:
   - Sample size < 5 returns INSUFFICIENT_PEER_DATA
6. Privacy constraints:
   - Never exposes individual peer balances, transactions, debt, or identities
7. REST API: GET /api/v1/businesses/{id}/context-intelligence
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.context_intelligence import ContextIntelligenceService
from src_py.models.context_schemas import ContextClassificationEnum

client = TestClient(app)


def test_example_1_industry_and_seasonal_downturn():
    """
    Example 1 from specification:
    Customer: -20%
    Industry: -18%
    Region: -17%
    Peers: -19%
    Classification: NORMAL_SEASONAL / INDUSTRY_WIDE
    """
    report = ContextIntelligenceService.evaluate_context_intelligence(
        customer_id="CUST_EX1",
        customer_growth_pct=-20.0,
        industry="TEXTILES",
        region="TAMIL_NADU",
        business_size="MSME",
        peer_sample_size=42,
        custom_industry_median=-18.0,
        custom_region_median=-17.0,
        custom_peer_median=-19.0,
        custom_seasonal_baseline=-16.0
    )

    # Acceptance Criteria Check: Classifies as NORMAL_SEASONAL or INDUSTRY_WIDE
    assert report.classification in [
        ContextClassificationEnum.NORMAL_SEASONAL,
        ContextClassificationEnum.INDUSTRY_WIDE
    ]
    # Abnormality score must be very low because customer is tracking peers
    assert report.abnormality_score < 20.0
    assert report.customer_vs_peer_deviation == -1.0  # -20 - (-19)
    assert report.confidence >= 0.85
    assert "synchronized sectoral" in report.explanation.lower() or "close alignment" in report.explanation.lower()


def test_example_2_customer_specific_abnormal_decline():
    """
    Example 2 from specification:
    Customer: -35%
    Industry: -7%
    Region: -9%
    Peers: -8%
    Classification: CUSTOMER_SPECIFIC
    """
    report = ContextIntelligenceService.evaluate_context_intelligence(
        customer_id="CUST_EX2",
        customer_growth_pct=-35.0,
        industry="TEXTILES",
        region="TAMIL_NADU",
        business_size="MSME",
        peer_sample_size=42,
        custom_industry_median=-7.0,
        custom_region_median=-9.0,
        custom_peer_median=-8.0,
        custom_seasonal_baseline=-5.0
    )

    # Acceptance Criteria Check: Distinguishes customer downturn with stable industry as CUSTOMER_SPECIFIC
    assert report.classification == ContextClassificationEnum.CUSTOMER_SPECIFIC
    # Abnormality score must be high
    assert report.abnormality_score >= 80.0
    assert report.customer_vs_peer_deviation == -27.0  # -35 - (-8)
    assert report.customer_vs_industry_deviation == -28.0
    assert "idiosyncratic" in report.explanation.lower() or "deviates" in report.explanation.lower()


def test_minimum_peer_rule_insufficient_data():
    """
    Verifies that peer populations under 5 trigger INSUFFICIENT_PEER_DATA
    rather than unrepresentative statistical extrapolation.
    """
    report = ContextIntelligenceService.evaluate_context_intelligence(
        customer_id="CUST_SMALL_POP",
        customer_growth_pct=-25.0,
        peer_sample_size=3  # Less than 5!
    )

    assert report.classification == ContextClassificationEnum.INSUFFICIENT_PEER_DATA
    assert "insufficient peer population" in report.explanation.lower()
    assert report.confidence == 0.0


def test_privacy_guarantee():
    """
    Ensures peer benchmarks contain ONLY aggregated medians and sample counts,
    and includes explicit DPDP Act privacy compliance notes.
    """
    report = ContextIntelligenceService.evaluate_context_intelligence(
        customer_id="CUST_PRIVACY",
        customer_growth_pct=-15.0,
        peer_sample_size=30
    )

    report_dict = report.model_dump()
    assert "privacy_compliance_note" in report_dict
    assert "DPDP Act" in report_dict["privacy_compliance_note"]
    # Verify no raw peer accounts or balances are present
    assert "peer_transactions" not in report_dict
    assert "peer_balances" not in report_dict
    assert "peer_identities" not in report_dict


def test_api_v1_context_intelligence_endpoint():
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/context-intelligence?customer_growth_pct=-32.0&peer_sample_size=35")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "classification" in data
    assert "abnormality_score" in data
    assert "industry_benchmark" in data
    assert "peer_cohort_benchmark" in data
    assert data["peer_sample_size"] == 35
