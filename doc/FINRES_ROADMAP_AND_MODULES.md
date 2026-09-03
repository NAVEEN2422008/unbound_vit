# FINRES: Detailed Module Breakdown & Execution Roadmap

**Document Title**: Comprehensive Module Engineering & Step-by-Step Implementation Roadmap  
**Platform**: **FINRES** (Financial Resilience & Distress Prevention Platform)  
**File Location**: `doc/FINRES_ROADMAP_AND_MODULES.md`  
**Target Environment**: India Stack Digital Public Infrastructure (DPI) & Bank-Grade Enterprise Architecture  
**Status**: Ready for Implementation

---

## 1. Complete Functional Module Architecture

The FINRES platform is engineered across **8 core decoupled modules**:

```
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 1: INGESTION & CONSENT GATEWAY (RBI AA, UPI NLP, GSTN, TReDS)                   │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 2: FINANCIAL REALITY ENGINE (FRE) & DUAL SCORING                                │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 3: CONTEXT-AWARE INTELLIGENCE ENGINE (CIE - Cluster & Seasonality)              │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 4: OBLIGATION COLLISION RADAR (OCR) & CASH RUNWAY                               │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 5: ASSET-LEVEL ECONOMIC ENGINE (ALE - Plant & Machinery Yield)                  │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 6: DECISION TWIN SIMULATOR & STRESS-TEST SANDBOX                                │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 7: LEAST-HARM INTERVENTION OPTIMIZER ("No-New-Loan" Rule)                       │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ MODULE 8: CONSENT-BASED B2B BUSINESS RECOVERY NETWORK (ONDC Native)                    │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Granular Module Specifications

### 🧩 MODULE 1: Ingestion & Consent Gateway
* **Purpose**: Secure, multi-source ingestion of structured and unstructured financial records without data tampering.
* **Core Components**:
  * **Sahamati AA Connector**: Connects to RBI-regulated Financial Information Providers (FIPs) to pull bank statements, credit card debts, and overdraft lines.
  * **UPI Semantic Parser**: NLP pipeline classifying unstructured remarks (e.g., `"vendor pay"`, `"diesel"`, `"salary"`) into essential vs. discretionary expenses.
  * **GSTN & E-Way Ingestion**: Reconciles GSTR-1 (invoices issued) vs GSTR-3B (taxes paid).
  * **Consent Manager**: Tracks granular, time-bound, revocable consent handles aligned with the DPDP Act 2023.

---

### 🧩 MODULE 2: Financial Reality Engine (FRE) & Dual Scoring
* **Purpose**: Builds a unified ground truth of customer liquidity and computes the dual risk metrics.
* **Core Components**:
  * **Multi-Lender Aggregator**: De-duplicates loans across multiple banks and fintech NBFCs to calculate true total debt burden.
  * **Data Completeness & Reliability Score ($0 - 100$)**:
    $$S_{completeness} = \sum w_i \cdot \text{Availability}(Stream_i) \times \text{Freshness}(Stream_i)$$
  * **Financial Health Score ($S_{health} \in [0, 100]$)**: Measures instantaneous solvency, liquid cash buffer, and debt-to-income ratio.

---

### 🧩 MODULE 3: Context-Aware Intelligence Engine (CIE)
* **Purpose**: Determines what "normal" financial behavior looks like by benchmarking against regional and sectoral clusters.
* **Core Components**:
  * **Cluster Baseline Analyzer**: Evaluates sector-specific hubs (e.g., *Tiruppur Knitwear*, *Surat Synthetic Textiles*, *Morbi Ceramics*, *Ludhiana Cycle Parts*).
  * **Seasonal Cycle Decoupler**: Adjusts expectations for monsoon slowdowns, harvest windows, and festival demand peaks.
  * **Contextual Distress Score ($S_{distress} \in [0, 100]$)**:
    $$S_{distress} = f\left( \frac{\Delta \text{Revenue}_{borrower} - \Delta \text{Revenue}_{cluster}}{\sigma_{cluster}} \right)$$
    Distinguishes a **benign seasonal dip** from **enterprise-specific structural failure**.

---

### 🧩 MODULE 4: Obligation Collision Radar (OCR) & Cash Runway
* **Purpose**: Provides date-specific forecasting of liquidity dry-up points.
* **Core Components**:
  * **Cash Trajectory Forecaster**: Projects daily net liquidity over 7, 15, 30, and 60 days:
    $$L(t) = L(0) + \sum_{\tau=1}^t \left( \hat{I}(\tau) - \hat{E}_{ess}(\tau) - \hat{O}_{fixed}(\tau) \right)$$
  * **Statutory Collision Detector**: Checks against recurring Indian stress dates (5th/10th NACH debits, 7th TDS, 15th Advance Tax/EPF, 20th GSTR-3B).
  * **Cash Runway & Critical Date Calculator**: Flags the exact day $t^*$ where $L(t^*) \le 0$.

---

### 🧩 MODULE 5: Asset-Level Economic Engine (ALE)
* **Purpose**: Isolates the profitability and loan burden of individual physical assets (machinery, vehicles, operating lines).
* **Core Components**:
  * **Machine EBITDA Attribution**:
    $$\text{Asset Net Contribution}_i = \text{Revenue Attributable}_i - \text{Operating Costs}_i - \text{Dedicated Term Loan EMI}_i$$
  * **Asset Classification**: Flags assets as *Productive*, *Marginal*, or *Cash-Bleeding*.
  * **Targeted Asset Remedies**: Recommends machine restructuring, subleasing idle capacity, or disposal rather than company-wide insolvency.

---

### 🧩 MODULE 6: Decision Twin Simulator & Stress-Test Sandbox
* **Purpose**: Runs counterfactual *"What-If"* simulations across candidate interventions.
* **Core Components**:
  * **Scenario Engine**:
    * *Option A: Emergency Working Capital Loan*
    * *Option B: EMI Tenor Extension (RBI MSME Framework)*
    * *Option C: TReDS Invoice Discounting (RXIL/Invoicemart)*
    * *Option D: Idle Asset Sale / Restructuring*
    * *Option E: Expense Trimming & Savings Ring-fencing*
  * **Stress-Testing Suite**: Tests borrower survival against a $10\%-20\%$ revenue drop, 30-day invoice delays, or interest rate hikes.

---

### 🧩 MODULE 7: Least-Harm Intervention Optimizer
* **Purpose**: Selects the intervention that restores financial resilience with minimum borrower harm.
* **Core Components**:
  * **Multi-Objective Optimizer**:
    $$\min_{k \in \mathcal{K}} \quad \text{HarmScore}(k) = w_1 \cdot \text{CostOfCapital}(k) + w_2 \cdot \Delta \text{Tenure}(k) + w_3 \cdot P(\text{Distress} \mid L^{(k)})$$
  * **Hard "No-New-Loan" Safety Guardrail**:
    $$\text{If } \text{DSCR}^{(k)} < 1.25 \text{ or } \text{FOIR}^{(k)} > 60\% \Longrightarrow \text{VETO NEW LOANS}.$$
  * **Intervention Sequencer**: Generates ordered action plans (*Today* $\rightarrow$ *This Week* $\rightarrow$ *Before Collision Date*).
  * **Intervention Evidence Card**: Generates auditable justification cards for 1-click Credit Officer approval.

---

### 🧩 MODULE 8: Consent-Based B2B Business Recovery Network
* **Purpose**: Addresses the underlying revenue/order shortage without adding debt.
* **Core Components**:
  * **Double-Blind Matching Algorithm**: Matches order-deficient MSMEs with bank corporate clients requiring suppliers based on product, capacity, and region.
  * **ONDC Interoperability**: Plugs into the Open Network for Digital Commerce to discover commercial opportunities.
  * **Privacy Protocol**: Zero exposure of financial distress data; introductions occur strictly upon mutual opt-in.

---

## 3. Step-by-Step Implementation Roadmap

```
                                  EXECUTION TIMELINE
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: FOUNDATION & SYNTHETIC DATA GENERATOR                                         │
│ • Database Schema (Prisma/PostgreSQL) • Synthetic Data Generator (1000+ Profiles)     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 2: CORE INTELLIGENCE ENGINES (FRE, CIE, OCR, ALE)                                │
│ • Dual Scoring Engine • Cluster Normalcy Decoupler • Obligation Collision Radar        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 3: SIMULATION & LEAST-HARM DECISION TWIN                                         │
│ • Decision Twin Sandbox • "No-New-Loan" Guardrail • Evidence Card Generator            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 4: UI/UX DASHBOARDS & DEMO SUITE                                                 │
│ • Bank Officer Command Center • MSME/Customer Portal • 3 Guided Demo Walkthroughs      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 🗓️ Phase 1: Foundation, Data Models & Data Generator
* **Task 1.1**: Define PostgreSQL schema via Prisma ORM for `Customer`, `Transaction`, `Loan`, `Obligation`, `Asset`, `IndustryBenchmark`, `Intervention`, and `AuditLog`.
* **Task 1.2**: Build a high-fidelity **Synthetic Data Generator** creating:
  * 1,000+ individual profiles (Salaried, Gig workers, Freelancers).
  * 200+ MSMEs across 5 Indian clusters (Tiruppur, Surat, Morbi, Ludhiana, Bengaluru).
  * 24–36 months of realistic time-series transaction histories including seasonality.

### 🗓️ Phase 2: Core Intelligence Engines (FRE, CIE, OCR, ALE)
* **Task 2.1**: Implement the **Financial Reality Engine (FRE)** to aggregate multi-lender debt, calculate liquidity runway, and compute the Data Completeness Score.
* **Task 2.2**: Implement the **Context Intelligence Engine (CIE)** with statistical z-score cluster benchmarking to decouple seasonal dips from structural default.
* **Task 2.3**: Build the **Obligation Collision Radar (OCR)** time-series pipeline to project cash curves and pinpoint the exact critical liquidity date.
* **Task 2.4**: Implement the **Asset-Level Economic Engine (ALE)** for machine-level EBITDA calculations.

### 🗓️ Phase 3: Decision Twin Simulator & Least-Harm Optimizer
* **Task 3.1**: Build the **Decision Twin Simulator** running counterfactual projections across Options A through E.
* **Task 3.2**: Implement the **"No-New-Loan" Guardrail** ($\text{DSCR} \ge 1.25$, $\text{FOIR} \le 60\%$) and the Least-Harm action sequencer.
* **Task 3.3**: Create the **Intervention Evidence Card** formatting engine for human credit officers.
* **Task 3.4**: Implement the prototype **B2B Business Opportunity Matcher** using anonymized similarity scoring.

### 🗓️ Phase 4: Bank-Grade Dashboard & Demonstration Suite
* **Task 4.1**: Build the **Bank Officer Command Center** (Portfolio health overview, sector stress heatmaps, customer distress triage, 1-click intervention approval).
* **Task 4.2**: Build the **MSME & Retail Customer Portal** (Financial health vs distress score, visual cash runway timeline, What-If simulator, dynamic Safe-to-Save recommendations).
* **Task 4.3**: Implement the **3 Core Interactive Demo Scenarios**:
  1. *MSME Textile Manufacturer* (Sri Balaji Fabrics, Tiruppur — Machine bleed + TReDS discounting).
  2. *Salaried Household* (Balloon school fee collision + EMI restructuring).
  3. *Gig Delivery Worker* (Monsoon earnings dip + Safe-to-Save micro-savings).

---

## 4. Verification & Demo Checklist

- [x] Supports all 11 customer archetypes (Salaried, Gig, MSME, Seasonal, etc.).
- [x] Decouples **Financial Health** from **Contextual Distress**.
- [x] Accurately forecasts cash-flow collision dates (15–45 days ahead).
- [x] Isolates machinery/asset-level EBITDA yields for MSMEs.
- [x] Mathematically blocks harmful credit via the **"No-New-Loan" Guardrail**.
- [x] Includes human-in-the-loop review with **Intervention Evidence Cards**.
- [x] Fully aligned with RBI Master Directions and India Stack DPI.
