"""
FINRES API Endpoint Tests.
Tests all HTTP endpoints for correctness, auth, and response format.
Run with: python -m pytest tests/test_api_endpoints.py -v
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from src_py.api.main import app
    c = TestClient(app)
    yield c
    c.cookies.clear()


# ───────────────────── Public Endpoints ─────────────────────
class TestPublicEndpoints:
    def test_health_check(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["status"] == "HEALTHY"

    def test_root_redirects(self, client):
        res = client.get("/")
        assert res.status_code in (302, 307, 200)

    def test_docs_disabled(self, client):
        res = client.get("/docs")
        assert res.status_code == 404

    def test_openapi_disabled(self, client):
        res = client.get("/openapi.json")
        assert res.status_code == 404

    def test_metrics_endpoint(self, client):
        res = client.get("/metrics")
        assert res.status_code == 200
        assert "finres_" in res.text or res.text == ""

    def test_metrics_summary_endpoint(self, client):
        res = client.get("/api/v1/metrics/summary")
        assert res.status_code == 200
        data = res.json()
        assert "counters" in data or "histograms" in data


# ───────────────────── Auth Endpoints ─────────────────────
class TestAuthEndpoints:
    def test_login_page_renders(self, client):
        res = client.get("/login")
        assert res.status_code == 200
        assert "login" in res.text.lower() or "password" in res.text.lower()

    def test_login_valid_demo(self, client):
        res = client.post("/login", data={"username": "demo", "password": "demo"}, follow_redirects=False)
        assert res.status_code in (302, 303, 307, 200)
        assert "finres_user" in res.cookies

    def test_login_invalid(self, client):
        res = client.post("/login", data={"username": "admin", "password": "wrong"}, follow_redirects=False)
        assert res.status_code in (200, 401, 302, 303)

    def test_logout_clears_session(self, client):
        client.post("/login", data={"username": "demo", "password": "demo"}, follow_redirects=False)
        res = client.get("/logout", follow_redirects=False)
        assert res.status_code in (302, 303, 307, 200)


# ───────────────────── Protected UI Routes ─────────────────────
class TestProtectedUIRoutes:
    def _auth_client(self, client):
        client.post("/login", data={"username": "demo", "password": "demo"}, follow_redirects=False)
        return client

    def test_dashboard_renders_with_auth(self, client):
        c = self._auth_client(client)
        res = c.get("/dashboard")
        assert res.status_code == 200
        assert "dashboard" in res.text.lower()

    def test_customers_list_renders(self, client):
        c = self._auth_client(client)
        res = c.get("/customers")
        assert res.status_code == 200

    def test_customer_detail_renders(self, client):
        c = self._auth_client(client)
        res = c.get("/customers/CUST_MSME_TIRUPPUR_001")
        assert res.status_code == 200
        assert "balaji" in res.text.lower() or "sri" in res.text.lower()

    def test_dashboard_without_auth_redirects(self, client):
        res = client.get("/dashboard", follow_redirects=False)
        assert res.status_code in (302, 303, 307)

    def test_monitoring_dashboard_renders(self, client):
        c = self._auth_client(client)
        res = c.get("/monitoring/dashboard")
        assert res.status_code == 200

    def test_monitoring_models_renders(self, client):
        c = self._auth_client(client)
        res = c.get("/monitoring/models")
        assert res.status_code == 200


# ───────────────────── API Endpoints ─────────────────────
class TestAPIEndpoints:
    def test_fre_analysis(self, client):
        res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/financial-reality")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

    def test_distress_prediction(self, client):
        res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/distress")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

    def test_cashflow_forecast(self, client):
        res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/cashflow/forecast")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

    def test_distress_classify(self, client):
        res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/distress/classify")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

    def test_financial_resilience(self, client):
        res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/financial-resilience")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

    def test_root_cause(self, client):
        res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/root-cause")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

    def test_prevention_report(self, client):
        res = client.get("/api/v1/prevention/CUST_MSME_TIRUPPUR_001")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

    def test_audit_log(self, client):
        res = client.get("/api/v1/audit/customer/CUST_MSME_TIRUPPUR_001")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

    def test_nonexistent_customer(self, client):
        res = client.get("/api/v1/customers/NONEXISTENT/distress")
        assert res.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
