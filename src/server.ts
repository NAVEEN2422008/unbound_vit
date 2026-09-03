import * as http from 'http';
import * as fs from 'fs';
import * as path from 'path';
import { generateCoreScenarios } from './data/generator';
import { FinresDiagnosticCoordinator } from './engines/coordinator';
import { LeastHarmOptimizer } from './engines/leastHarmOptimizer';
import { BusinessRecoveryNetwork } from './engines/businessRecoveryNetwork';
import { DecisionTwinSimulator } from './engines/decisionTwinSimulator';
import { GovernanceFairnessMonitor } from './engines/governanceFairnessMonitor';

const PORT = process.env.PORT || 3000;
const scenarios = generateCoreScenarios();

// Additional realistic demo profiles matching the master prompt specifications
const additionalProfiles = [
  {
    id: 'CUST_TEMP_LIQ_004',
    name: 'Kaveri Precision Tools LLP',
    archetype: 'MSME',
    clusterRegion: 'Ludhiana',
    occupationOrIndustry: 'Engineering & Bicycle Parts',
    consent: { isConsented: true, dataCompletenessPercentage: 92, lastConsentTimestamp: '2026-09-01T08:00:00Z' },
    financialReality: {
      currentLiquidBalance: 85000,
      monthlyAverageIncome: 1450000,
      monthlyEssentialExpenses: 1180000,
      totalMonthlyDebtObligation: 195000,
      totalOutstandingDebt: 2200000,
      cashRunwayDays: 12,
      criticalLiquidityDate: '2026-09-14',
      incomeVolatilityRatio: 0.15
    },
    scores: { financialHealthScore: 68, contextualDistressScore: 52, distressStatus: 'VULNERABLE', confidencePercentage: 92 },
    loans: [
      { id: 'LOAN_KAV_01', customerId: 'CUST_TEMP_LIQ_004', lenderName: 'Punjab National Bank', lenderType: 'SCHEDULED_COMMERCIAL_BANK', loanType: 'WORKING_CAPITAL_CASH_CREDIT', principalAmount: 2000000, outstandingPrincipal: 1750000, interestRateAnnual: 11.2, monthlyEmi: 195000, tenureMonthsRemaining: 18, nachDebitDate: 14, dpd: 0, isAssetBacked: false }
    ],
    obligations: [
      { id: 'OBL_RENT_KAV', customerId: 'CUST_TEMP_LIQ_004', category: 'Factory Lease', amount: 95000, dueDayOfMonth: 5, isMandatory: true },
      { id: 'OBL_WAGES_KAV', customerId: 'CUST_TEMP_LIQ_004', category: 'Machinist Wages', amount: 480000, dueDayOfMonth: 7, isMandatory: true },
      { id: 'OBL_POWER_KAV', customerId: 'CUST_TEMP_LIQ_004', category: 'PSPCL Industrial Power', amount: 140000, dueDayOfMonth: 18, isMandatory: true }
    ],
    receivables: [
      { id: 'REC_KAV_01', invoiceNumber: 'INV/2026/092', debtorName: 'Hero Cycles Tier-1 Vendor Unit', amount: 420000, dueDate: '2026-09-18', status: 'OVERDUE', isTredsEligible: true }
    ],
    assets: [
      { id: 'ASSET_CNC_1', customerId: 'CUST_TEMP_LIQ_004', name: '5-Axis CNC Milling Unit', type: 'MACHINE', purchaseCost: 3500000, monthlyOperatingCost: 190000, monthlyAttributableRevenue: 340000, utilizationRatePercentage: 86, status: 'PRODUCTIVE' }
    ]
  },
  {
    id: 'CUST_SEASONAL_MORBI_005',
    name: 'Somnath Vitrified Tiles Pvt Ltd',
    archetype: 'SEASONAL_BUSINESS',
    clusterRegion: 'Morbi',
    occupationOrIndustry: 'Ceramics & Sanitaryware',
    consent: { isConsented: true, dataCompletenessPercentage: 95, lastConsentTimestamp: '2026-09-01T08:00:00Z' },
    financialReality: {
      currentLiquidBalance: 320000,
      monthlyAverageIncome: 4200000,
      monthlyEssentialExpenses: 3600000,
      totalMonthlyDebtObligation: 480000,
      totalOutstandingDebt: 5800000,
      cashRunwayDays: 24,
      criticalLiquidityDate: '2026-09-28',
      incomeVolatilityRatio: 0.32
    },
    scores: { financialHealthScore: 62, contextualDistressScore: 38, distressStatus: 'WATCH', confidencePercentage: 94 },
    loans: [
      { id: 'LOAN_SOM_01', customerId: 'CUST_SEASONAL_MORBI_005', lenderName: 'Bank of Baroda', lenderType: 'SCHEDULED_COMMERCIAL_BANK', loanType: 'TERM_LOAN_MACHINERY', principalAmount: 4500000, outstandingPrincipal: 3800000, interestRateAnnual: 10.8, monthlyEmi: 280000, tenureMonthsRemaining: 32, nachDebitDate: 10, dpd: 0, isAssetBacked: true },
      { id: 'LOAN_SOM_02', customerId: 'CUST_SEASONAL_MORBI_005', lenderName: 'HDFC Bank', lenderType: 'SCHEDULED_COMMERCIAL_BANK', loanType: 'WORKING_CAPITAL_CASH_CREDIT', principalAmount: 2500000, outstandingPrincipal: 2000000, interestRateAnnual: 11.5, monthlyEmi: 200000, tenureMonthsRemaining: 12, nachDebitDate: 25, dpd: 0, isAssetBacked: false }
    ],
    obligations: [
      { id: 'OBL_GAS_SOM', customerId: 'CUST_SEASONAL_MORBI_005', category: 'Gujarat Gas Piped Supply', amount: 980000, dueDayOfMonth: 12, isMandatory: true },
      { id: 'OBL_PAYROLL_SOM', customerId: 'CUST_SEASONAL_MORBI_005', category: 'Kiln Staff Payroll', amount: 820000, dueDayOfMonth: 7, isMandatory: true }
    ],
    receivables: [
      { id: 'REC_SOM_01', invoiceNumber: 'INV/ST/841', debtorName: 'Kajaria Regional Depot Dealer', amount: 850000, dueDate: '2026-09-25', status: 'CURRENT', isTredsEligible: true }
    ],
    assets: [
      { id: 'ASSET_KILN_A', customerId: 'CUST_SEASONAL_MORBI_005', name: 'Continuous Tunnel Kiln Line 1', type: 'MACHINE', purchaseCost: 7500000, monthlyOperatingCost: 1150000, monthlyAttributableRevenue: 1950000, utilizationRatePercentage: 91, status: 'PRODUCTIVE' }
    ]
  }
];

const allCustomerProfiles = [...scenarios, ...additionalProfiles];

const server = http.createServer((req, res) => {
  const parsedUrl = new URL(req.url || '/', `http://${req.headers.host}`);
  const pathname = parsedUrl.pathname;

  // API Route: Get All Profiles
  if (pathname === '/api/profiles') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
    return res.end(JSON.stringify(allCustomerProfiles));
  }

  // API Route: Run Diagnostic on Profile
  if (pathname.startsWith('/api/diagnose/')) {
    const custId = pathname.replace('/api/diagnose/', '');
    const profile = allCustomerProfiles.find(s => s.id === custId) || allCustomerProfiles[0];
    
    // In seasonal case, pass appropriate current month and drop
    const isMorbi = profile.clusterRegion === 'Morbi';
    const drop = isMorbi ? -18.0 : -24.0;
    const month = isMorbi ? 7 : 9;
    
    const diag = FinresDiagnosticCoordinator.diagnoseCustomer(profile, drop, month);
    const opt = LeastHarmOptimizer.optimizeInterventions(profile);
    const b2b = BusinessRecoveryNetwork.findOpportunitiesForSupplier(profile.id);

    res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
    return res.end(JSON.stringify({ diagnostic: diag, optimization: opt, b2bMatches: b2b }));
  }

  // API Route: Get Governance Audit Ledger & Fairness Metrics
  if (pathname === '/api/governance') {
    const ledger = GovernanceFairnessMonitor.getAuditLedger();
    const fairness = GovernanceFairnessMonitor.computeCohortFairnessMetrics();
    res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
    return res.end(JSON.stringify({ auditLedger: ledger, fairnessCohorts: fairness }));
  }

  // API Route: Approve / Record Officer Decision
  if (pathname === '/api/governance/approve' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body);
        const record = GovernanceFairnessMonitor.recordOfficerDecision(
          payload.customerId,
          payload.actionTaken || 'APPROVED',
          payload.approvedByOfficer || 'R. K. Sundaram (Chief Credit Officer, Commercial Banking)',
          payload.officerRole || 'CREDIT_OFFICER',
          payload.recommendedStrategy || 'TReDS Discounting & Loan Restructure',
          payload.guardrailStatus || 'NO_NEW_LOAN_VETO_ENFORCED',
          payload.modificationNotes
        );
        res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        return res.end(JSON.stringify({ success: true, record }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ error: 'Invalid payload' }));
      }
    });
    return;
  }

  // Serve Main UI
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(renderCoreBankingPortalHtml());
});

function renderCoreBankingPortalHtml(): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>FINRES — Commercial Credit Early Distress Prevention System</title>
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&family=Consolas:wght@400;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

  <style>
    /* ==========================================================================
       AUTHENTIC INDIAN SCHEDULED COMMERCIAL BANK CORE BANKING INTERFACE
       Design Rule: Strict institutional utility. Zero decorative glows or gradients.
       Clean borders, standard tabular grid, high data density, clear auditing trail.
       ========================================================================== */
    :root {
      --c-navy-dark: #002b49;     /* Standard State Bank / Nationalised Bank Deep Navy */
      --c-navy-mid: #003e6b;
      --c-blue-link: #0056b3;
      --c-gray-bg: #eceff1;       /* Standard government/banking portal background */
      --c-panel-bg: #ffffff;
      --c-bar-gray: #e0e4e8;
      --c-border-grid: #cfd8dc;
      --c-border-dark: #90a4ae;
      
      --c-text-primary: #212529;
      --c-text-secondary: #495057;
      --c-text-muted: #6c757d;
      
      --c-safe-bg: #e8f5e9;
      --c-safe-text: #1b5e20;
      --c-safe-border: #a5d6a7;
      
      --c-warn-bg: #fff8e1;
      --c-warn-text: #b78103;
      --c-warn-border: #ffe082;
      
      --c-danger-bg: #ffebee;
      --c-danger-text: #b71c1c;
      --c-danger-border: #ef9a9a;
      
      --font-base: 'Segoe UI', Arial, sans-serif;
      --font-mono: 'Consolas', 'Lucida Console', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
      background-color: var(--c-gray-bg);
      color: var(--c-text-primary);
      font-family: var(--font-base);
      font-size: 12.5px;
      line-height: 1.4;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* Standard Bank Utility Header */
    .gov-topbar {
      background: #001f35;
      color: #cfd8dc;
      font-size: 11px;
      padding: 3px 20px;
      display: flex;
      justify-content: space-between;
      border-bottom: 1px solid #002b49;
    }
    .main-header {
      background: var(--c-navy-dark);
      color: #ffffff;
      padding: 8px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 2px solid #0056b3;
    }
    .header-branding {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .bank-logo {
      background: #ffffff;
      color: var(--c-navy-dark);
      font-weight: 800;
      font-size: 14px;
      padding: 3px 8px;
      border-radius: 2px;
      border: 1px solid #ffffff;
      letter-spacing: 0.5px;
    }
    .title-block h1 {
      font-size: 15px;
      font-weight: 700;
      letter-spacing: -0.2px;
    }
    .title-block p {
      font-size: 11px;
      color: #b0bec5;
    }
    .header-status {
      display: flex;
      align-items: center;
      gap: 16px;
      font-size: 11.5px;
    }
    .badge-status {
      background: #004d40;
      color: #80cbc4;
      border: 1px solid #00695c;
      padding: 2px 8px;
      border-radius: 2px;
      font-weight: 600;
    }

    /* Action & Customer Ribbon */
    .subnav-ribbon {
      background: #ffffff;
      border-bottom: 1px solid var(--c-border-grid);
      padding: 8px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .customer-selector {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .customer-selector label {
      font-weight: 700;
      color: var(--c-navy-dark);
      text-transform: uppercase;
      font-size: 11px;
    }
    .account-tabs {
      display: flex;
      gap: 4px;
    }
    .acc-tab {
      background: #f1f3f5;
      border: 1px solid var(--c-border-grid);
      padding: 5px 12px;
      font-size: 11.5px;
      font-weight: 600;
      color: var(--c-text-secondary);
      cursor: pointer;
      border-radius: 2px;
    }
    .acc-tab:hover {
      background: #e9ecef;
      color: #000;
    }
    .acc-tab.active {
      background: var(--c-navy-mid);
      color: #ffffff;
      border-color: var(--c-navy-dark);
    }
    .compliance-indicators {
      display: flex;
      gap: 6px;
      font-size: 11px;
    }
    .comp-tag {
      background: #eef2f6;
      border: 1px solid #cfd8dc;
      padding: 2px 8px;
      border-radius: 2px;
      color: #37474f;
      font-weight: 600;
    }

    /* Main Operational Workstation */
    .portal-workstation {
      flex: 1;
      padding: 14px 20px;
      max-width: 1720px;
      margin: 0 auto;
      width: 100%;
      display: grid;
      grid-template-columns: 350px 1fr 410px;
      gap: 14px;
    }
    .column-stack {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    /* Core Banking Card Specification */
    .panel-card {
      background: var(--c-panel-bg);
      border: 1px solid var(--c-border-grid);
      border-radius: 3px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.03);
      display: flex;
      flex-direction: column;
    }
    .panel-header {
      background: #f8f9fa;
      border-bottom: 1px solid var(--c-border-grid);
      padding: 8px 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .panel-header h2 {
      font-size: 12px;
      font-weight: 700;
      color: var(--c-navy-dark);
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    .panel-content {
      padding: 12px;
    }

    /* Standard Core Banking Data Grid */
    .bank-grid {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    .bank-grid th {
      background: #f1f3f5;
      color: #37474f;
      text-align: left;
      padding: 6px 8px;
      border: 1px solid var(--c-border-grid);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }
    .bank-grid td {
      padding: 6px 8px;
      border: 1px solid var(--c-border-grid);
    }
    .bank-grid tr:nth-child(even) {
      background: #fafbfc;
    }

    /* Data Metric Cells */
    .grid-label { color: var(--c-text-secondary); }
    .grid-val { font-weight: 600; text-align: right; color: var(--c-text-primary); }
    .val-mono { font-family: var(--font-mono); font-weight: 700; }

    /* Dual Index Indicators */
    .index-matrix {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 10px;
    }
    .index-box {
      background: #f8f9fa;
      border: 1px solid var(--c-border-grid);
      padding: 8px;
      text-align: center;
      border-radius: 2px;
    }
    .index-score {
      font-size: 22px;
      font-weight: 700;
      margin: 2px 0;
      font-family: var(--font-mono);
    }
    .index-label {
      font-size: 10px;
      font-weight: 700;
      color: var(--c-text-muted);
      text-transform: uppercase;
    }

    /* Severity Indicators */
    .tag-danger { background: var(--c-danger-bg); color: var(--c-danger-text); border: 1px solid var(--c-danger-border); font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 2px; }
    .tag-warning { background: var(--c-warn-bg); color: var(--c-warn-text); border: 1px solid var(--c-warn-border); font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 2px; }
    .tag-safe { background: var(--c-safe-bg); color: var(--c-safe-text); border: 1px solid var(--c-safe-border); font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 2px; }

    /* Trajectory Timeline Chart */
    .chart-container {
      height: 180px;
      width: 100%;
      margin-bottom: 10px;
    }
    .schedule-log {
      max-height: 155px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }
    .log-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 5px 8px;
      background: #f8f9fa;
      border: 1px solid #e9ecef;
      font-size: 11px;
    }
    .log-item.item-critical {
      background: var(--c-danger-bg);
      border-color: var(--c-danger-border);
    }

    /* Interventions & Counterfactual Sandbox */
    .intervention-block {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .sim-option {
      border: 1px solid var(--c-border-grid);
      padding: 8px 10px;
      background: #ffffff;
      border-radius: 2px;
    }
    .sim-option.vetoed {
      background: #fff8f8;
      border-color: #ef9a9a;
    }
    .sim-option.approved {
      background: #f4faf4;
      border-color: #a5d6a7;
    }
    .sim-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 3px;
    }
    .sim-title {
      font-size: 11.5px;
      font-weight: 700;
      color: var(--c-navy-dark);
    }
    .sim-body {
      font-size: 11px;
      color: var(--c-text-secondary);
      line-height: 1.35;
    }
    .sim-metrics {
      display: flex;
      gap: 10px;
      margin-top: 5px;
      font-size: 10px;
      font-family: var(--font-mono);
      font-weight: 700;
    }

    /* Ordered Action Sequence */
    .action-sequence {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .action-step {
      display: flex;
      gap: 8px;
      padding: 7px 9px;
      background: #f8f9fa;
      border: 1px solid var(--c-border-grid);
      align-items: flex-start;
    }
    .step-tag {
      background: var(--c-navy-mid);
      color: #ffffff;
      font-size: 9px;
      font-weight: 700;
      padding: 2px 5px;
      border-radius: 2px;
      white-space: nowrap;
    }

    /* Approval & Mandate Execution */
    .btn-mandate {
      background: var(--c-navy-mid);
      color: #ffffff;
      border: 1px solid var(--c-navy-dark);
      padding: 9px 14px;
      font-size: 12px;
      font-weight: 700;
      border-radius: 2px;
      cursor: pointer;
      width: 100%;
      margin-top: 10px;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    .btn-mandate:hover {
      background: var(--c-navy-dark);
    }

    /* Footer Legal Notice */
    footer {
      background: #e9ecef;
      color: #6c757d;
      font-size: 10.5px;
      text-align: center;
      padding: 8px;
      border-top: 1px solid var(--c-border-grid);
    }
  </style>
</head>
<body>

  <!-- Top Institutional Bar -->
  <div class="gov-topbar">
    <span>Department of Banking Operations & Development · Reserve Bank of India</span>
    <span>Terminal: <strong>DBOD-PRUD-MUM-01</strong> · Secure Session</span>
  </div>

  <header class="main-header">
    <div class="header-branding">
      <div class="bank-logo">FINRES</div>
      <div class="title-block">
        <h1>PRUDENTIAL DISTRESS PREVENTION & RESOLUTION PORTAL</h1>
        <p>Early Financial Distress Identification, Obligation Collision Radar & Non-Debt Resolution Engine</p>
      </div>
    </div>
    <div class="header-status">
      <span class="badge-status">● SAHAMATI AA ACTIVE</span>
      <span>GSTN Invoice Link: <strong>VERIFIED</strong></span>
      <span>Officer: <strong>R. K. Sundaram (Chief Credit Officer)</strong></span>
    </div>
  </header>

  <!-- Borrower Navigation & Compliance Ribbon -->
  <nav class="subnav-ribbon">
    <div class="customer-selector">
      <label>Portfolio Account:</label>
      <div class="account-tabs">
        <button class="acc-tab active" onclick="loadAccount('CUST_MSME_TIRUPPUR_001', this)">Sri Balaji Fabrics (MSME Textile)</button>
        <button class="acc-tab" onclick="loadAccount('CUST_TEMP_LIQ_004', this)">Kaveri Tools (Temporary Liquidity Gap)</button>
        <button class="acc-tab" onclick="loadAccount('CUST_SEASONAL_MORBI_005', this)">Somnath Tiles (Seasonal Dip)</button>
        <button class="acc-tab" onclick="loadAccount('CUST_SALARIED_BLR_002', this)">Ananya Sharma (Retail Salaried)</button>
        <button class="acc-tab" onclick="loadAccount('CUST_GIG_BLR_003', this)">Ravi Kumar (Platform Delivery)</button>
      </div>
    </div>
    <div class="compliance-indicators">
      <span class="comp-tag">DPDP Act (2023) Section 6</span>
      <span class="comp-tag">Prudential DSCR Floor: 1.25</span>
      <span class="comp-tag">Double-Blind ONDC B2B</span>
    </div>
  </nav>

  <!-- 3-Column Banking Layout -->
  <main class="portal-workstation">
    
    <!-- LEFT COLUMN: Module 1 & Module 7 (Balance Sheet & Regional Calibration) -->
    <div class="column-stack">
      
      <!-- Module 1: Financial Reality Engine -->
      <div class="panel-card">
        <div class="panel-header">
          <h2>Borrower Solvency Ledger (FRE)</h2>
          <span class="tag-warning" id="txt-distress-status">VULNERABLE</span>
        </div>
        <div class="panel-content">
          <div class="index-matrix">
            <div class="index-box">
              <div class="index-label">Solvency Health</div>
              <div class="index-score" id="txt-health-score" style="color: #1b5e20;">58</div>
              <div style="font-size: 9.5px; color: var(--c-text-muted);">Scale: 0–100</div>
            </div>
            <div class="index-box">
              <div class="index-label">Contextual Distress</div>
              <div class="index-score" id="txt-distress-score" style="color: #b71c1c;">84</div>
              <div style="font-size: 9.5px; color: var(--c-text-muted);">Velocity Divergence</div>
            </div>
          </div>

          <table class="bank-grid">
            <tr>
              <td class="grid-label">Total Debt Outstanding</td>
              <td class="grid-val val-mono" id="txt-total-debt">₹38,00,000</td>
            </tr>
            <tr>
              <td class="grid-label">Monthly Debt Service (EMI)</td>
              <td class="grid-val val-mono" id="txt-monthly-emi">₹3,20,000</td>
            </tr>
            <tr>
              <td class="grid-label">Liquid Bank Balances</td>
              <td class="grid-val val-mono" id="txt-liquid-balance">₹1,40,000</td>
            </tr>
            <tr>
              <td class="grid-label">True Cash Runway</td>
              <td class="grid-val val-mono" id="txt-cash-runway" style="color: #b78103;">19 Days</td>
            </tr>
            <tr>
              <td class="grid-label">Sahamati AA Completeness</td>
              <td class="grid-val" id="txt-completeness">94% (Consented)</td>
            </tr>
          </table>
        </div>
      </div>

      <!-- Module 7: Context-Aware Intelligence Engine -->
      <div class="panel-card">
        <div class="panel-header">
          <h2>Regional Cluster Calibration (CIE)</h2>
          <span style="font-size: 11px; font-weight: 700; color: #37474f;" id="txt-cluster-name">Tiruppur Cluster</span>
        </div>
        <div class="panel-content">
          <p style="font-size: 11px; color: var(--c-text-secondary); margin-bottom: 10px; line-height: 1.4;" id="txt-cie-diagnostic">
            Calibrating borrower against regional cluster benchmark...
          </p>

          <table class="bank-grid">
            <tr>
              <td class="grid-label">Borrower MoM Revenue</td>
              <td class="grid-val val-mono" id="txt-borrower-mom" style="color: #b71c1c;">-24.0%</td>
            </tr>
            <tr>
              <td class="grid-label">Regional Cluster Average</td>
              <td class="grid-val val-mono" id="txt-cluster-mom">-5.0%</td>
            </tr>
            <tr>
              <td class="grid-label">Abnormal Divergence</td>
              <td class="grid-val val-mono" id="txt-cluster-deviation" style="color: #b71c1c;">-19.0%</td>
            </tr>
            <tr>
              <td class="grid-label">Risk Classification</td>
              <td class="grid-val" id="txt-seasonal-status" style="font-weight: 700;">Structural Default Risk</td>
            </tr>
          </table>
        </div>
      </div>

    </div>

    <!-- CENTER COLUMN: Module 2, 3, 11 (Cash-Flow Radar & Asset-Level Economics) -->
    <div class="column-stack">
      
      <!-- Module 2 & 3: Obligation Collision Radar -->
      <div class="panel-card">
        <div class="panel-header">
          <h2>Obligation Collision Radar (30-Day Liquidity Horizon)</h2>
          <span class="tag-danger" id="txt-collision-summary">Collision: 19 Days</span>
        </div>
        <div class="panel-content">
          <div class="chart-container">
            <canvas id="cashTrajectoryChart"></canvas>
          </div>
          <div class="schedule-log" id="schedule-log-container">
            <!-- Timeline log rows -->
          </div>
        </div>
      </div>

      <!-- Module 11: Asset-Level Financial Intelligence -->
      <div class="panel-card">
        <div class="panel-header">
          <h2>Machinery & Production Line Economics (ALE)</h2>
          <span class="tag-danger" id="txt-asset-flag">1 Bleeding Asset</span>
        </div>
        <div class="panel-content" style="padding: 6px 12px 12px 12px;">
          <div id="asset-grid-container">
            <!-- Machinery breakdown table -->
          </div>
        </div>
      </div>

    </div>

    <!-- RIGHT COLUMN: Module 16, 18, 19, 25 (Decision Twin, Least-Harm & Mandate) -->
    <div class="column-stack">
      
      <!-- Module 18: Decision Twin Simulator & Module 16: No-New-Loan Guardrail -->
      <div class="panel-card">
        <div class="panel-header">
          <h2>Decision Twin Counterfactual Sandbox</h2>
          <span style="font-size: 10px; font-weight: 700; color: #546e7a;">PRUDENTIAL DSCR ≥ 1.25</span>
        </div>
        <div class="panel-content">
          <div class="intervention-block" id="twin-options-container">
            <!-- Counterfactual options -->
          </div>
        </div>
      </div>

      <!-- Module 19 & 25: Least-Harm Action Plan & Human Approval -->
      <div class="panel-card">
        <div class="panel-header">
          <h2>Ordered Resolution Plan</h2>
          <span class="tag-safe">PRUDENTIAL MANDATE</span>
        </div>
        <div class="panel-content">
          <div class="action-sequence" id="action-sequence-container">
            <!-- Action steps -->
          </div>

          <button class="btn-mandate" onclick="executePrudentialMandate()">
            Approve & Execute Resolution Mandate
          </button>
        </div>
      </div>

    </div>

  </main>

  <!-- Institutional Compliance Footer -->
  <footer>
    FINRES Institutional Credit Platform · Built in compliance with Reserve Bank of India Master Directions on Prudential Norms on Income Recognition, Asset Classification and Provisioning (IRACP) & Digital Personal Data Protection Act (2023).
  </footer>

  <script>
    let activeCustomerId = 'CUST_MSME_TIRUPPUR_001';
    let chartInstance = null;
    let cachedOptimization = null;

    async function loadAccount(custId, btnElem) {
      activeCustomerId = custId;
      if (btnElem) {
        document.querySelectorAll('.acc-tab').forEach(b => b.classList.remove('active'));
        btnElem.classList.add('active');
      }

      const res = await fetch('/api/diagnose/' + custId);
      const payload = await res.json();
      const diag = payload.diagnostic;
      const opt = payload.optimization;
      cachedOptimization = opt;

      // Update Left Panel: FRE Solvency
      document.getElementById('txt-health-score').innerText = diag.financialReality.financialHealthScore;
      document.getElementById('txt-distress-score').innerText = diag.contextIntelligence.contextualDistressScore;
      document.getElementById('txt-total-debt').innerText = '₹' + diag.financialReality.totalOutstandingDebt.toLocaleString('en-IN');
      document.getElementById('txt-monthly-emi').innerText = '₹' + diag.financialReality.totalMonthlyDebtEmi.toLocaleString('en-IN');
      document.getElementById('txt-liquid-balance').innerText = '₹' + diag.financialReality.currentLiquidBalance.toLocaleString('en-IN');
      document.getElementById('txt-cash-runway').innerText = diag.financialReality.cashRunwayDays + ' Days';
      document.getElementById('txt-completeness').innerText = diag.financialReality.dataCompletenessPercentage + '% (Consented)';
      
      const badgeElem = document.getElementById('txt-distress-status');
      badgeElem.innerText = diag.contextIntelligence.distressStatus;
      badgeElem.className = diag.contextIntelligence.distressStatus === 'CRITICAL' ? 'tag-danger' : diag.contextIntelligence.distressStatus === 'VULNERABLE' ? 'tag-warning' : 'tag-safe';

      // Update Left Panel: CIE Cluster Calibration
      document.getElementById('txt-cluster-name').innerText = diag.contextIntelligence.clusterRegion + ' (' + diag.contextIntelligence.industryOrOccupation + ')';
      document.getElementById('txt-cie-diagnostic').innerText = diag.contextIntelligence.diagnosticExplanation;
      document.getElementById('txt-borrower-mom').innerText = diag.contextIntelligence.customerGrowthMomPercentage + '%';
      document.getElementById('txt-cluster-mom').innerText = (diag.contextIntelligence.clusterGrowthMomPercentage > 0 ? '+' : '') + diag.contextIntelligence.clusterGrowthMomPercentage + '%';
      document.getElementById('txt-cluster-deviation').innerText = diag.contextIntelligence.deviationFromClusterPercentage + '%';
      document.getElementById('txt-seasonal-status').innerText = diag.contextIntelligence.isSeasonalDip ? 'Benign Seasonal Pattern' : 'Structural Default Risk';

      // Update Center Panel: Obligation Radar Chart
      document.getElementById('txt-collision-summary').innerText = diag.collisionRadar.criticalLiquidityDate 
        ? 'Collision: ' + diag.collisionRadar.criticalLiquidityDate 
        : 'Sufficient Buffer';

      drawBankTrajectoryChart(diag.collisionRadar.projections);

      const logContainer = document.getElementById('schedule-log-container');
      logContainer.innerHTML = '';
      diag.collisionRadar.projections.slice(0, 15).forEach(p => {
        const item = document.createElement('div');
        item.className = 'log-item' + (p.isCollision ? ' item-critical' : '');
        item.innerHTML = \`
          <div>
            <span style="font-family:var(--font-mono); font-weight:700;">\${p.dateStr}</span> · 
            <span style="color:var(--c-text-secondary);">\${p.scheduledEvents.length > 0 ? p.scheduledEvents.join(' | ') : 'Regular Operations Outflow'}</span>
          </div>
          <div style="font-family:var(--font-mono); font-weight:700; color:\${p.closingBalance < 0 ? '#b71c1c' : '#1b5e20'}">
            ₹\${p.closingBalance.toLocaleString('en-IN')}
          </div>
        \`;
        logContainer.appendChild(item);
      });

      // Update Center Panel: Machinery Asset Table
      const assetGridContainer = document.getElementById('asset-grid-container');
      if (diag.assetDiagnostic.assetBreakdown.length > 0) {
        document.getElementById('txt-asset-flag').innerText = diag.assetDiagnostic.lossMakingAssetsCount + ' Cash-Bleeding Machine';
        document.getElementById('txt-asset-flag').style.display = 'inline-block';
        let gridHtml = \`
          <table class="bank-grid">
            <thead>
              <tr>
                <th>Machine</th>
                <th>Revenue</th>
                <th>Operating Cost</th>
                <th>Loan EMI</th>
                <th>Net Yield</th>
              </tr>
            </thead>
            <tbody>
        \`;
        diag.assetDiagnostic.assetBreakdown.forEach(a => {
          gridHtml += \`
            <tr>
              <td style="font-weight:600;">\${a.name}</td>
              <td class="val-mono">₹\${a.monthlyAttributableRevenue.toLocaleString('en-IN')}</td>
              <td class="val-mono">₹\${a.monthlyOperatingCost.toLocaleString('en-IN')}</td>
              <td class="val-mono">₹\${a.monthlyDedicatedEmi.toLocaleString('en-IN')}</td>
              <td class="val-mono" style="font-weight:700; color:\${a.netMonthlyContribution < 0 ? '#b71c1c' : '#1b5e20'}">
                \${a.netMonthlyContribution < 0 ? '-₹' + Math.abs(a.netMonthlyContribution).toLocaleString('en-IN') : '+₹' + a.netMonthlyContribution.toLocaleString('en-IN')}
              </td>
            </tr>
          \`;
        });
        gridHtml += '</tbody></table>';
        assetGridContainer.innerHTML = gridHtml;
      } else {
        document.getElementById('txt-asset-flag').style.display = 'none';
        assetGridContainer.innerHTML = '<div style="font-size:11px; color:var(--c-text-muted); padding:6px 0;">Retail / Platform Worker Account (No physical machinery or equipment assets registered).</div>';
      }

      // Update Right Panel: Decision Twin Simulator
      const twinContainer = document.getElementById('twin-options-container');
      twinContainer.innerHTML = '';
      opt.allSimulatedOptions.forEach(op => {
        const item = document.createElement('div');
        item.className = 'sim-option' + (!op.isPermissibleUnderGuardrail ? ' vetoed' : op.harmLevel === 'LOW' ? ' approved' : '');
        item.innerHTML = \`
          <div class="sim-head">
            <span class="sim-title">\${op.title}</span>
            <span class="\${!op.isPermissibleUnderGuardrail ? 'tag-danger' : 'tag-safe'}">
              \${!op.isPermissibleUnderGuardrail ? 'VETOED (DSCR < 1.25)' : 'PERMISSIBLE'}
            </span>
          </div>
          <div class="sim-body">\${op.description}</div>
          <div class="sim-metrics">
            <span style="color:\${!op.isPermissibleUnderGuardrail ? '#b71c1c' : '#1b5e20'}">
              \${!op.isPermissibleUnderGuardrail ? op.guardrailViolationReason : 'Projected DSCR: ' + op.projectedDscr}
            </span>
            <span>Runway: \${op.cashRunwayDays}d</span>
          </div>
        \`;
        twinContainer.appendChild(item);
      });

      // Update Right Panel: Ordered Action Sequence
      const actionContainer = document.getElementById('action-sequence-container');
      actionContainer.innerHTML = '';
      opt.actionSequence.forEach(st => {
        const row = document.createElement('div');
        row.className = 'action-step';
        row.innerHTML = \`
          <div class="step-tag">\${st.timeframe}</div>
          <div>
            <div style="font-weight:600; color:var(--c-navy-dark);">\${st.action}</div>
            <div style="font-size:10px; color:#1b5e20; font-weight:600; margin-top:1px;">Impact: \${st.expectedImpact} (\${st.responsibleParty})</div>
          </div>
        \`;
        actionContainer.appendChild(row);
      });
    }

    function drawBankTrajectoryChart(projections) {
      const ctx = document.getElementById('cashTrajectoryChart').getContext('2d');
      const labels = projections.slice(0, 20).map(p => p.dateStr.slice(5));
      const balances = projections.slice(0, 20).map(p => p.closingBalance);

      if (chartInstance) chartInstance.destroy();

      chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Liquidity Balance (₹)',
            data: balances,
            borderColor: '#003e6b',
            backgroundColor: 'rgba(0, 62, 107, 0.04)',
            fill: true,
            tension: 0.05,
            pointRadius: 2.5,
            pointBackgroundColor: balances.map(b => b < 0 ? '#b71c1c' : '#1b5e20'),
            borderWidth: 1.5
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => '₹' + ctx.parsed.y.toLocaleString('en-IN')
              }
            }
          },
          scales: {
            x: {
              grid: { color: '#cfd8dc' },
              ticks: { color: '#546e7a', font: { size: 9.5 } }
            },
            y: {
              grid: { color: '#cfd8dc' },
              ticks: {
                color: '#546e7a',
                font: { size: 9.5 },
                callback: (val) => '₹' + (val / 1000) + 'k'
              }
            }
          }
        }
      });
    }

    async function executePrudentialMandate() {
      if (!cachedOptimization) return;
      const res = await fetch('/api/governance/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customerId: activeCustomerId,
          actionTaken: 'APPROVED',
          approvedByOfficer: 'R. K. Sundaram (Chief Credit Officer, SME Hub Tiruppur)',
          recommendedStrategy: cachedOptimization.recommendedOption.title,
          guardrailStatus: cachedOptimization.evidenceCard.guardrailStatus,
          modificationNotes: 'Approved via FINRES Core Banking System with digital cryptographic signature.'
        })
      });
      const data = await res.json();
      if (data.success) {
        alert('✅ Restructuring Plan Approved & Logged in Audit Ledger!\\n\\nAudit Reference: ' + data.record.auditId + '\\nDigital Signature: ' + data.record.digitalSignatureHash);
      }
    }

    window.onload = () => loadAccount('CUST_MSME_TIRUPPUR_001');
  </script>
</body>
</html>`;
}

server.listen(PORT, () => {
  console.log(`====================================================`);
  console.log(`  🚀 FINRES PLATFORM LIVE AT: http://localhost:${PORT}`);
  console.log(`====================================================`);
});
