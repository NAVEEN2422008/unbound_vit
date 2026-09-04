# FINRES — Financial Resilience & Distress Prevention Platform

> Institutional Scheduled Commercial Bank (SCB) early warning, distress prevention, and intervention engine for Indian MSMEs and retail borrowers under RBI IRACP norms and DPDP Act 2023 compliance.

**Version:** 2.0.0  
**Stack:** Python 3.13 · FastAPI · SQLAlchemy · scikit-learn · TypeScript · Node.js  
**License:** Academic / Internal Use

---

## Table of Contents

- [What FINRES Does](#what-finres-does)
- [Architecture Overview](#architecture-overview)
- [Three Portals](#three-portals)
- [27 Service Engines](#27-service-engines)
- [ML Pipeline & Models](#ml-pipeline--models)
- [API Reference (70+ Endpoints)](#api-reference-70-endpoints)
- [Database Schema](#database-schema)
- [Authentication & RBAC](#authentication--rbac)
- [Observability & Monitoring](#observability--monitoring)
- [Feature Store & Drift Detection](#feature-store--drift-detection)
- [Notifications](#notifications)
- [Deployment](#deployment)
- [Local Development](#local-development)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Sample Data](#sample-data)
- [Regulatory Compliance](#regulatory-compliance)

---

## What FINRES Does

FINRES is a decision-support platform that helps bank officers identify, prevent, and manage financial distress in MSME and retail borrower accounts. It ingests raw financial data, runs 27 analytical engines, scores distress with ML models trained on 182K real-world records, and presents actionable recommendations through three role-specific portals.

**Core problems it solves:**
- Invisible cash flow distress (businesses look healthy on paper but are days from default)
- Wrong intervention timing (too early wastes resources, too late loses recovery)
- Generic advice (one-size-fits-all restructuring fails for seasonal businesses)
- Regulatory non-compliance (RBI IRACP, DPDP Act 2023 audit requirements)
- Information asymmetry (bank officer sees 10% of the borrower's financial reality)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        THREE PORTALS                            │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │ Banker Portal │  │ Customer Portal  │  │ Monitoring Portal │  │
│  │  /dashboard   │  │ /customer/*      │  │ /monitoring/*     │  │
│  └──────┬───────┘  └────────┬─────────┘  └─────────┬─────────┘  │
└─────────┼───────────────────┼───────────────────────┼────────────┘
          │                   │                       │
          ▼                   ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI APPLICATION                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Auth Middleware (cookie + API key + RBAC)               │   │
│  │  Request Context Middleware (X-Request-ID, timing)       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              27 SERVICE ENGINES                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │   FRE    │ │Cashflow  │ │Distress  │ │Root Cause│   │   │
│  │  │  Engine  │ │ Timeline │ │Detection │ │ Analyzer │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │Collision │ │ Context  │ │ Seasonal │ │  Peer    │   │   │
│  │  │  Radar   │ │Intel     │ │ Forecast │ │Benchmark │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │  Asset   │ │Receivabl.│ │ Credit   │ │Financing │   │   │
│  │  │Intellig. │ │Analysis  │ │Affordab. │ │ Timing   │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │Decision  │ │ Least    │ │ Non-Debt │ │Business  │   │   │
│  │  │  Twin    │ │  Harm    │ │ Recovery │ │Matching  │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │Confidence│ │Explain   │ │ Banker   │ │ Consent  │   │   │
│  │  │  Engine  │ │Assistant │ │ Review   │ │ Service  │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                │   │
│  │  │  Audit   │ │Outcome   │ │Prevention│                │   │
│  │  │  Ledger  │ │ Verif.   │ │ Service  │                │   │
│  │  └──────────┘ └──────────┘ └──────────┘                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                ML PIPELINE (4 Models)                     │   │
│  │  GradientBoost(AUC=0.798) · RF Enriched · RF · Logistic │   │
│  │  Trained on 182K records from 3 real-world datasets      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FEATURE STORE · MODEL MONITOR · EXPLAINABILITY · NOTIFY │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SQLAlchemy ORM (SQLite → PostgreSQL) · Structured Logs  │   │
│  │  Prometheus Metrics · 51 Passing Tests                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Dual-stack:** The Python FastAPI backend (primary) runs all 27 engines. A separate TypeScript Node.js server (`src/server.ts`) provides a standalone prototype dashboard with 9 TypeScript engine reimplementations for demo purposes.

---

## Three Portals

### 1. Banker Portal (Bank Officers)
- **`/dashboard`** — Portfolio-wide metrics: total customers, average distress score, distress distribution, high-risk alerts, recent predictions
- **`/customers`** — Sortable customer table with archetype, region, distress score, trend, last prediction date
- **`/customers/{id}`** — Full customer detail with 13 module tabs: Financial Reality, Cashflow, Collisions, Distress, Classification, Root Cause, Context, Seasonal, Peer, Assets, Resilience, Confidence, Explanation

### 2. Customer Portal (Borrowers)
- **`/customer/dashboard`** — Personal resilience dashboard, distress score, cash buffer, recommendations, notification feed
- **`/customer/detail`** — Detail view with loan breakdown, obligations, and consent management

### 3. Monitoring Portal (Risk Administrators)
- **`/monitoring/dashboard`** — System health, model metrics, prediction throughput, alert summary
- **`/monitoring/models`** — Model management: view active/inactive models, accuracy metrics, enable/disable
- **`/monitoring/rules`** — Rule threshold management (DSCR, FOIR, cash buffer limits)
- **`/monitoring/audit`** — Immutable audit log viewer with hash-chain verification

---

## 27 Service Engines

Each engine is a standalone service with deterministic logic, testable independently.

### Core Analysis Engines
| # | Engine | File | What It Does |
|---|--------|------|-------------|
| 1 | **Financial Reality Engine (FRE)** | `fre_engine.py` | Transaction normalization, cash categorization, ratio computation, data provenance tracking (ACTUAL/USER_ENTERED/PREDICTED/ESTIMATED) |
| 2 | **Cash-Flow Timeline** | `cashflow_engine.py` | Daily/weekly cash movement analysis, 30/60/90-day forward forecasts, cash buffer days |
| 3 | **Obligation Collision Radar** | `collision_radar.py` | Calendar-date obligation collision detection, severity classification (GREEN/YELLOW/ORANGE/RED), shortfall quantification |
| 4 | **Early Distress Detection** | `distress_engine.py` | Rule-based + ML distress scoring, gradient boosting inference, risk level classification |
| 5 | **Distress Classifier** | `distress_classifier.py` | Classifies dominant distress type: LIQUIDITY_GAP, INCOME_SHOCK, DEBT_OVERLOAD, EXPENSE_SHOCK, MIXED |
| 6 | **Root-Cause Analyzer** | `root_cause_engine.py` | Evaluates 13 candidate causes, ranks by contribution score, provides personalized root causes per archetype |

### Context & Benchmarking Engines
| # | Engine | File | What It Does |
|---|--------|------|-------------|
| 7 | **Context Intelligence** | `context_intelligence.py` | Classifies decline as SEASONAL, INDUSTRY_WIDE, REGION_WIDE, or CUSTOMER_SPECIFIC |
| 8 | **Seasonal Forecasting** | `seasonal_forecasting.py` | Time-series decomposition (moving average, multiplicative indices, Holt-Winters), 12-month forecast |
| 9 | **Peer Benchmarking** | `peer_benchmarking.py` | 8-metric peer comparison with N>=5 minimum peer rule, cluster-based peer selection |

### Asset & Receivable Engines
| # | Engine | File | What It Does |
|---|--------|------|-------------|
| 10 | **Asset Financial Intelligence** | `asset_intelligence.py` | Machine-level economics, net contribution, utilization analysis, multi-scenario simulation (7 paths) |
| 11 | **Receivables Analysis** | `receivable_analysis.py` | Payment date prediction, collection probability scoring, 7/14/30-day cash forecasts |

### Credit & Financing Engines
| # | Engine | File | What It Does |
|---|--------|------|-------------|
| 12 | **Credit Affordability** | `credit_affordability.py` | "Can the customer repay safely?" analysis with DSCR >= 1.25 guardrail |
| 13 | **No-New-Loan Guardrail** | `credit_affordability.py` | Prevents new loan origination if DSCR would fall below 1.25 |
| 14 | **Financing Timing** | `financing_timing.py` | WHEN to borrow: BORROW_NOW, LATER, USE_RECEIVABLE_FINANCING, AVOID |

### Decision & Optimization Engines
| # | Engine | File | What It Does |
|---|--------|------|-------------|
| 15 | **Decision Digital Twin** | `decision_twin.py` | 11 intervention scenarios across 3/6/12/24-month horizons with guardrail checks |
| 16 | **Least-Harm Optimizer** | `least_harm_optimizer.py` | Multi-dimensional harm/benefit scoring, anti-predatory guardrails, evidence cards |
| 17 | **Non-Debt Recovery** | `non_debt_recovery.py` | 8 non-debt recovery levers: customer diversification, receivable collection, cost reduction, etc. |

### Matching & Explainability Engines
| # | Engine | File | What It Does |
|---|--------|------|-------------|
| 18 | **Business Opportunity Matching** | `business_matching.py` | Double-blind B2B matching with mutual consent (DPDP compliant), anonymized profiles |
| 19 | **Confidence Engine** | `confidence_engine.py` | 7-dimension epistemic confidence scoring (data completeness, freshness, model confidence, etc.) |
| 20 | **Explanation Assistant** | `explanation_assistant.py` | Zero-hallucination plain-language explanations generated from deterministic engine outputs |

### Governance & Compliance Engines
| # | Engine | File | What It Does |
|---|--------|------|-------------|
| 21 | **Banker Human Review** | `banker_review_service.py` | Review screen assembly, escalation detection, officer decision recording |
| 22 | **Consent Service** | `consent_service.py` | DPDP Act 2023 consent lifecycle: GRANTED, PENDING, REVOKED, EXPIRED, NOT_REQUIRED |
| 23 | **Immutable Audit Ledger** | `audit_ledger_service.py` | SHA-256 hash-chained immutable audit trail, 9 event types, tamper detection |
| 24 | **Outcome Verification** | `outcome_verification_service.py` | Before/after comparison, SUCCESS/PARTIAL/NO_EFFECT/NEGATIVE classification |
| 25 | **Prevention Efficacy** | `prevention_service.py` | Longitudinal prevention reporting at 30/60/90/180-day horizons |

### Infrastructure Engines
| # | Engine | File | What It Does |
|---|--------|------|-------------|
| 26 | **Customer Dashboard** | `customer_dashboard.py` | Aggregates all engine outputs into customer-facing dashboard data |
| 27 | **Data Ingestion** | `data_ingestion.py` | CSV/JSON parsing, validation, duplicate detection, completeness scoring, quarantine |

---

## ML Pipeline & Models

### Training Data

| Dataset | Records | Features | Source |
|---------|---------|----------|--------|
| `credit_risk.csv` | 32,581 | 12 | Kaggle `laotse/credit-risk-dataset` |
| `loan_default.csv` | 148,670 | 14 | Kaggle `yasserh/loan-default-dataset` |
| `german_credit.csv` | 1,000 | 20 | UCI Machine Learning Repository |

**Total after merge:** 182,251 records. Default rate: ~24%.

### Feature Engineering

**9 base features** from raw financial inputs:
- `declining_cash_pct` — Cash balance decline trend
- `neg_balance_freq` — Frequency of negative balance days
- `cash_buffer_days` — Days of runway at current burn rate
- `revenue_decline_pct` — Revenue decline percentage
- `income_volatility` — Income standard deviation
- `fixed_cost_ratio` — Fixed costs / total expenses
- `debt_service_ratio` — Debt service / income
- `late_payments` — Overdue payment count
- `collision_shortfall_scaled` — Obligation collision severity

**19 enriched features** (interaction + transformation):
- `income_per_year_exp`, `collateral_coverage`, `loan_burden`, `ltv_x_grade`
- `log_income`, `log_property`, `score_x_income`, `risk_volatility`, etc.

### Trained Models

| Model | Accuracy | AUC | F1 | Features | File |
|-------|----------|-----|-----|----------|------|
| Logistic Regression | 76.4% | 0.595 | 0.101 | 9 | `distress_logistic.joblib` |
| Random Forest | 76.7% | 0.625 | 0.136 | 9 | `distress_random_forest.joblib` |
| **Gradient Boosting** | **85.6%** | **0.798** | **0.596** | **28** | `distress_gradient_boost.joblib` |
| Enriched Random Forest | 85.6% | 0.794 | 0.595 | 28 | `distress_rf_enriched.joblib` |

**Best model:** Gradient Boosting (`distress_gradient_boost`) — deployed as primary predictor.

### Pipeline Components

| File | Purpose |
|------|---------|
| `data_loader.py` | Loads 3 CSV datasets, unifies schema, handles missing values, deduplication |
| `features.py` | Feature engineering pipeline: base + enriched interaction features |
| `trainer.py` | Stratified train/test (80/20), 5-fold cross-validation, saves `.joblib` + metrics JSON |
| `registry.py` | `ModelRegistry` singleton — loads `.joblib` files, serves `predict()` and `predict_proba()` |
| `run_pipeline.py` | CLI runner: `python -m src_py.ai.run_pipeline` |
| `feature_store.py` | LRU cache with file persistence, hash-based versioning, get-or-compute pattern |
| `model_monitor.py` | PSI drift detection, prediction distribution tracking, anomaly scoring, health dashboard |
| `explainability.py` | SHAP-style feature importance, human-readable risk summaries per prediction |

### Retraining

```bash
# Download fresh datasets
python -m src_py.ai.download_data

# Retrain all models
python -m src_py.ai.run_pipeline

# Models saved to src_py/ai/model_artifacts/
```

---

## API Reference (70+ Endpoints)

All API endpoints return a standardized envelope:

```json
{
  "success": true,
  "message": "...",
  "data": { ... },
  "errors": [],
  "meta": {
    "execution_time_ms": 12.5,
    "model_version": "v2.1-prod",
    "rule_version": "RBI-IRACP-2026-R04",
    "customer_id": "CUST_MSME_TIRUPPUR_001",
    "confidence_score": 0.87,
    "data_completeness_pct": 92.0
  }
}
```

### System & Observability

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check for Render/load balancers |
| GET | `/metrics` | Prometheus-compatible metrics (counters, histograms, gauges) |
| GET | `/api/v1/metrics/summary` | Human-readable metrics summary |

### Data Ingestion

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/data/transactions/import` | Ingest and normalize transactions (JSON/CSV) |
| POST | `/api/v1/data/loans/import` | Normalize multi-lender loan data |
| POST | `/api/v1/data/assets/import` | Normalize fixed asset data |
| GET | `/api/v1/data/quality/{customer_id}` | Data completeness & quality report |

### Financial Reality Engine

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/customers/{id}/financial-reality` | Unified FinancialState |
| GET | `/api/v1/customers/{id}/financial-reality/metrics` | Ratio metrics block |
| POST | `/api/v1/customers/{id}/financial-reality/recalculate` | Counterfactual recalculation with simulated deltas |

### Cashflow & Obligations

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/customers/{id}/cashflow` | Daily/weekly cashflow timeline |
| GET | `/api/v1/customers/{id}/cashflow/forecast` | 30/60/90-day forward forecast |
| GET | `/api/v1/customers/{id}/obligation-collisions` | Calendar collision detection |

### Distress Detection

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/distress/predict` | Predict from request body |
| GET | `/api/v1/customers/{id}/distress` | Live distress from customer state |
| GET | `/api/v1/customers/{id}/distress/classify` | Classify dominant distress type |
| GET | `/api/v1/customers/{id}/financial-resilience` | 7-dimension resilience score |
| GET | `/api/v1/customers/{id}/root-cause` | 13-cause root-cause diagnosis |

### Context, Seasonal & Peer

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/businesses/{id}/context-intelligence` | Seasonal/industry/regional classification |
| GET | `/api/v1/businesses/{id}/seasonal-forecast` | 12-month seasonal forecast |
| GET | `/api/v1/businesses/{id}/peer-benchmark` | 8-metric peer comparison |

### Assets & Receivables

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/businesses/{id}/assets` | All business assets analysis |
| GET | `/api/v1/assets/{asset_id}/analysis` | Single asset analysis |
| POST | `/api/v1/assets/{id}/decision-simulation` | Multi-scenario simulation (7 paths) |
| GET | `/api/v1/businesses/{id}/receivables-analysis` | Trade receivable payment prediction |

### Credit & Financing

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/credit/affordability` | Can the customer repay safely? |
| POST | `/api/v1/credit/no-new-loan-check` | No-New-Loan Guardrail (DSCR >= 1.25) |
| GET | `/api/v1/businesses/{id}/financing-timing` | WHEN to borrow analysis |

### Decision & Optimization

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/decision-twin/simulate` | Simulate all 11 intervention scenarios |
| POST | `/api/v1/decision-twin/compare` | Compare candidate scenarios |
| GET | `/api/v1/decision-twin/{customer_id}` | Full digital twin report |
| POST | `/api/v1/interventions/optimize` | Least-harm optimization |
| GET | `/api/v1/businesses/{id}/non-debt-recovery` | 8 non-debt recovery levers |

### Business Matching & Explainability

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/business-matching/search` | Search anonymized B2B profiles |
| POST | `/api/v1/business-matching/{id}/consent` | Consent flow (5 statuses) |
| GET | `/api/v1/business-matching/{customer_id}` | All matches for customer |
| POST | `/api/v1/confidence/evaluate` | 7-dimension confidence evaluation |
| GET | `/api/v1/customers/{id}/confidence` | Customer confidence from FRE |
| POST | `/api/v1/explain/risk` | Plain-language risk explanation |
| POST | `/api/v1/explain/intervention` | Plain-language intervention explanation |

### Human Review & Audit

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/banker/review/{id}` | Full banker review screen |
| POST | `/api/v1/banker/review/{id}` | Submit banker decision |
| GET | `/api/v1/audit/customer/{id}` | Immutable audit trail (9 event types) |
| POST | `/api/v1/audit/events` | Record audit event |

### Outcome & Prevention

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/interventions/{id}/outcome` | Solvency outcome verification |
| POST | `/api/v1/interventions/{id}/outcome` | Record before/after outcome |
| GET | `/api/v1/prevention/{customer_id}` | Longitudinal prevention report |

### Consent Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/consents` | List consent records |
| POST | `/api/v1/consents` | Create consent |
| DELETE | `/api/v1/consents/{id}` | Revoke consent |

### Monitoring API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/monitoring/models/{model_id}/activate` | Activate model version |
| POST | `/monitoring/models/{model_id}/disable` | Disable model version |
| POST | `/monitoring/models/version` | Update model version |
| POST | `/monitoring/rules/threshold` | Update rule threshold |
| POST | `/monitoring/quality/{issue_id}/resolve` | Resolve data quality issue |

---

## Database Schema

SQLite locally (auto-upgrades to PostgreSQL via `DATABASE_URL` env var). 13 tables auto-created on startup.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `customers` | Core customer records | `id`, `name`, `archetype`, `pan_masked`, `cluster_region` |
| `bank_transactions` | Normalized transactions | `customer_id`, `amount`, `direction`, `category`, `channel` |
| `loans` | Multi-lender loan positions | `lender_name`, `principal_amount`, `outstanding_principal`, `monthly_emi` |
| `fixed_obligations` | Rent, payroll, tax, utilities | `category`, `amount`, `due_day_of_month`, `is_mandatory` |
| `receivables` | Trade invoices | `invoice_number`, `amount`, `due_date`, `status` |
| `payables` | Vendor payments | `vendor_name`, `amount`, `due_date`, `is_critical_supply` |
| `asset_financings` | Fixed assets with dedicated loans | `asset_name`, `purchase_cost`, `utilization_percentage` |
| `financial_realities` | Computed financial state snapshots | All ratio metrics, cash buffer, data completeness |
| `audit_log_entries` | Immutable audit trail | `cryptographic_hash`, `human_decision`, `final_action` |
| `outcome_monitoring_records` | Intervention effectiveness tracking | `baseline_distress_score`, `current_distress_score`, `default_averted` |
| `ingestion_batches` | Data upload tracking | `records_processed`, `records_accepted`, `data_completeness_score` |
| `ingestion_errors` | Quarantined/rejected rows | `error_type`, `error_message`, `raw_record` |
| `data_quality_reports` | Completeness & freshness scoring | `reliability_verdict`, `details_json` |

### Repository Pattern

```python
from src_py.db.engine import session_scope
from src_py.db.repository import CustomerRepository

with session_scope() as db:
    repo = CustomerRepository(db)
    customers = repo.get_by_archetype("MSME", limit=10)
    customer = repo.get("CUST_MSME_TIRUPPUR_001")
```

---

## Authentication & RBAC

### UI Authentication (Cookie-Based Session)

| Username | Password | Role | Display Name |
|----------|----------|------|-------------|
| `demo` | `demo` | BANKER | Demo User |
| `officer` | `finres2026` | BANKER | Bank Officer |
| `analyst` | `finres2026` | ANALYST | Risk Analyst |
| `admin` | `admin123` | ADMIN | System Admin |

Session cookies: `finres_user`, `finres_role`, `finres_name`

### API Authentication (X-API-KEY Header)

| API Key | User ID | Role | Permissions |
|---------|---------|------|-------------|
| `FINRES_CREDIT_OFFICER_KEY_2026` | OFFICER_BALA_772 | BANKER | read:portfolio, write:restructure, write:intervene |
| `FINRES_BANKER_KEY_2026` | BANKER_SUNDARAM_01 | BANKER | read:portfolio, write:restructure, write:intervene |
| `FINRES_RISK_ANALYST_KEY_2026` | ANALYST_MEERA_109 | BANKER | read:portfolio, read:diagnostics, simulate:twin |
| `FINRES_ADMIN_KEY_2026` | ADMIN_SYSTEM_ROOT | ADMIN | read:all, write:all, admin:all |
| `FINRES_AUDITOR_DPDP_KEY_2026` | AUDITOR_RBI_441 | ADMIN | read:audit_logs, read:governance, verify:dpdp |
| `FINRES_CUSTOMER_PORTAL_KEY_2026` | CUST_PORTAL_USER | CUSTOMER | read:dashboard, write:consent |

### RBAC Enforcement

```python
# Example: Admin-only endpoint
@app.post("/monitoring/models/version", dependencies=[Depends(require_roles(["ADMIN"]))])

# Example: Banker or Admin
@app.get("/api/v1/banker/review/{id}", dependencies=[Depends(require_roles(["BANKER", "ADMIN"]))])
```

---

## Observability & Monitoring

### Structured JSON Logging

Every log line is machine-parseable JSON:
```json
{
  "ts": "2026-09-04T03:14:53.331330Z",
  "level": "INFO",
  "logger": "finres.api",
  "msg": "POST /api/v1/distress/predict -> 200",
  "request_id": "a25f6043-c98c-4b37-8c50-36afb1165b85",
  "duration_ms": 12.5,
  "status_code": 200,
  "user_id": "demo"
}
```

### Prometheus Metrics

`GET /metrics` exports:
- `finres_http_requests_total` — Request count by method, path, status
- `finres_http_request_duration_seconds` — Latency histogram (p50, p95, p99)
- `finres_distress_predictions_total` — Prediction count by model
- `finres_model_inference_seconds` — Model inference latency
- `finres_active_customers` — Active customer gauge

### Request Tracing

Every request gets:
- `X-Request-ID` header (UUID)
- `X-Response-Time-MS` header
- Structured log entry with full context

---

## Feature Store & Drift Detection

### Feature Store

- **LRU in-memory cache** with file-backed persistence
- **Hash-based versioning** — same input always produces same cache key
- **get_or_compute pattern** — transparent cache-aside with automatic population
- **Statistics** — hit rate, cache size, miss count

```python
from src_py.ai.feature_store import get_feature_store

store = get_feature_store()
features = store.get_or_compute(
    customer_id="CUST_001",
    feature_version="enriched_v1",
    input_data=raw_financials,
    compute_fn=my_feature_computer
)
```

### Model Monitoring (Drift Detection)

- **PSI (Population Stability Index)** — detects prediction distribution shift
- **Anomaly detection** — flags scores outside [0, 1] range
- **Health dashboard** — per-model score mean, std, latency percentiles
- **Alert generation** — automatic `DriftAlert` objects with severity levels

```python
from src_py.ai.model_monitor import get_model_monitor

monitor = get_model_monitor()
monitor.record_prediction("gradient_boost", score=0.73, latency_ms=12.5)
alert = monitor.check_drift("gradient_boost")  # Returns DriftAlert if PSI > 0.05
```

---

## Notifications

### Notification Types

| Type | Trigger | Priority |
|------|---------|----------|
| `DISTRESS_ALERT` | Score exceeds threshold | HIGH / CRITICAL |
| `SCORE_CHANGE` | Score delta > 0.1 | MEDIUM |
| `INTERVENTION_RECOMMENDED` | Engine recommends action | MEDIUM |
| `MODEL_DRIFT` | PSI > 0.05 | MEDIUM / HIGH |
| `AUDIT_REQUIRED` | Human review needed | HIGH |
| `POLICY_VIOLATION` | Guardrail breach | HIGH |
| `SLA_BREACH` | Response time exceeded | HIGH |
| `SYSTEM_ERROR` | Engine failure | CRITICAL |

### Usage

```python
from src_py.services.notification_service import alert_distress, get_notification_store

# Auto-creates notification if score > threshold
alert_distress(customer_id="CUST_001", score=0.85, threshold=0.7)

# Query notifications
store = get_notification_store()
unread = store.unread_count()
all_notifs = store.get_all(unread_only=True, limit=20)
store.mark_read(notification_id="abc123")
```

---

## Deployment

### Render (Current Production)

```yaml
# render.yaml
services:
  - type: web
    name: finres-api
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src_py.api.main:app --host 0.0.0.0 --port $PORT --workers 1
    healthCheckPath: /health
```

**URL:** https://unbound-vit.onrender.com

### Docker

```bash
# Build
docker build -t finres .

# Run
docker run -p 8000:8000 -e DATABASE_URL="sqlite:///./finres.db" finres

# With PostgreSQL
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/finres" \
  finres
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./finres.db` | Database connection string |
| `PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `FEATURE_STORE_DIR` | `src_py/ai/feature_cache` | Feature cache directory |
| `MONITOR_DIR` | `src_py/ai/monitor_data` | Model monitoring data |
| `NOTIFICATION_DIR` | `src_py/data/notifications` | Notification persistence |

---

## Local Development

### Prerequisites
- Python 3.13+
- Node.js 18+ (for TypeScript server only)

### Setup

```bash
# Clone
git clone https://github.com/NAVEEN2422008/unbound_vit.git
cd unbound_vit

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn src_py.api.main:app --reload --host 0.0.0.0 --port 8000

# Open in browser
# Banker Portal: http://localhost:8000/dashboard
# Customer Portal: http://localhost:8000/customer/dashboard
# Monitoring: http://localhost:8000/monitoring/dashboard
# API Docs: http://localhost:8000/health
```

### TypeScript Server (Standalone Demo)

```bash
npm install
npx tsc
node dist/src/server.js
# Opens at http://localhost:3000
```

---

## Testing

### Python Tests (51 tests, all passing)

```bash
# Run all tests
python -m pytest tests/ -v

# Run core service tests only
python -m pytest tests/test_core_services.py -v

# Run API endpoint tests only
python -m pytest tests/test_api_endpoints.py -v
```

### Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_core_services.py` | 26 | Feature store, explainability, model monitor, notifications, integration |
| `test_api_endpoints.py` | 25 | Public endpoints, auth, protected UI routes, all API endpoints |

### Legacy TypeScript Tests

```bash
cd test/
npx tsx phase1_test.ts
npx tsx phase2_test.ts
npx tsx phase3_test.ts
npx tsx real_world_stress_test.ts
```

---

## Project Structure

```
vit/
├── src_py/                          # Python FastAPI Backend
│   ├── api/main.py                  # 3,515 lines, 70+ routes
│   ├── core/                        # Auth (RBAC) + Response envelope
│   ├── data/                        # Sample data, matching directory
│   ├── db/                          # SQLAlchemy engine + repository pattern
│   ├── models/                      # 30 Pydantic schemas + 13 DB tables
│   ├── services/                    # 27 service engines
│   ├── ai/                          # ML pipeline (4 models, 182K records)
│   │   ├── data/                    # Training CSVs
│   │   ├── model_artifacts/         # .joblib models + config
│   │   ├── feature_store.py         # LRU cache with persistence
│   │   ├── model_monitor.py         # Drift detection
│   │   └── explainability.py        # SHAP-style explanations
│   ├── observability/               # Logging, metrics, middleware
│   └── templates/                   # 12 Jinja2 HTML templates
├── src/                             # TypeScript Standalone Server
│   ├── server.ts                    # Node.js HTTP server + SPA
│   ├── types/models.ts              # TypeScript interfaces
│   ├── data/                        # Synthetic data generator
│   └── engines/                     # 9 TypeScript engine reimplementations
├── tests/                           # Python pytest (51 tests)
├── tests_py/                        # 35 individual service test files
├── doc/                             # Specifications, roadmaps, transcripts
├── data/                            # Benchmarks, profiles (JSON)
├── Dockerfile                       # Python 3.13-slim container
├── render.yaml                      # Render.com deployment config
├── requirements.txt                 # 12 Python dependencies
└── runtime.txt                      # Python 3.13
```

---

## Sample Data

### Customer 1: MSME (Tiruppur, Tamil Nadu)
- **ID:** `CUST_MSME_TIRUPPUR_001`
- **Name:** Sri Balaji Fabrics & Knits Pvt Ltd
- **Archetype:** MSME, Industry: Textiles & Apparel
- **Liquid Cash:** Rs 1,40,000 | **Savings:** Rs 50,000
- **Loans:** SBI Term Loan (Rs 25L) + Canara Working Capital (Rs 20L)
- **Obligations:** Rent, payroll, power, GST
- **Receivables:** Rs 12L overdue from buyer
- **Assets:** 3 machines including loss-making "Imported Terry Jacquard Unit" (34% utilization)

### Customer 2: Salaried (Bengaluru, Karnataka)
- **ID:** `CUST_SALARIED_BLR_002`
- **Name:** Ananya Sharma
- **Archetype:** SALARIED, Industry: IT
- **Liquid Cash:** Rs 18,500 | **Savings:** Rs 12,000
- **Loans:** HDFC Personal Loan (Rs 3.5L) + ICICI Credit Card (Rs 95K at 38% APR)
- **Obligations:** School tuition balloon fee (Rs 42K)

---

## Regulatory Compliance

### RBI IRACP (Income Recognition & Asset Classification Policy)
- **DSCR >= 1.25** — enforced as hard guardrail in credit affordability and No-New-Loan checks
- **FOIR <= 60%** — fixed obligation to income ratio enforced across all lending decisions
- **Classification triggers** — distress score > 0.7 triggers SMA-1-like early warning
- **Audit trail** — every decision logged with model version, rule version, and confidence score

### DPDP Act 2023 (Digital Personal Data Protection)
- **Consent lifecycle** — 5 states: GRANTED, PENDING, REVOKED, EXPIRED, NOT_REQUIRED
- **Double-blind matching** — business profiles anonymized before cross-party sharing
- **Right to erasure** — consent revocation triggers data anonymization
- **Immutable audit** — SHA-256 hash-chained records for regulatory inspection

### Fair Lending
- **Least-harm principle** — optimizer penalizes disproportionate impact on vulnerable archetypes
- **Anti-predatory guardrails** — prevents loan stacking, excessive interest burden
- **Explainability** — every ML prediction accompanied by feature importance breakdown

---

## Key Design Decisions

1. **Deterministic-first** — All 27 engines use deterministic, auditable logic. ML models augment but never replace rule-based decisions.
2. **Zero hallucination** — Explanation assistant generates plain-language text only from verified engine outputs, never from LLM generation.
3. **Dual-mode auth** — API key for machine-to-machine, cookie session for browser-based portals.
4. **Envelope pattern** — Every API response wraps data in `StandardAPIResponse[T]` with metadata (execution time, model version, confidence).
5. **Graceful degradation** — If ML models fail to load, the system falls back to rule-based scoring.
6. **Immutable audit** — Audit entries are SHA-256 hash-chained. Any tampering breaks the chain and is detectable.
