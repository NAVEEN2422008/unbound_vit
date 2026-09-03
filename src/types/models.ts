/**
 * FINRES Core Type Definitions & Data Model (India DPI & Global Standards)
 */

export type CustomerArchetype =
  | 'SALARIED'
  | 'SELF_EMPLOYED'
  | 'GIG_WORKER'
  | 'FREELANCER'
  | 'PROFESSIONAL'
  | 'HOUSEHOLD'
  | 'TRADER'
  | 'MSME'
  | 'MANUFACTURER'
  | 'SEASONAL_BUSINESS';

export type DistressStatus = 'HEALTHY' | 'WATCH' | 'VULNERABLE' | 'STRESSED' | 'CRITICAL';

export type TransactionCategory =
  | 'INCOME_SALARY'
  | 'INCOME_BUSINESS'
  | 'INCOME_GIG_PLATFORM'
  | 'INCOME_RECEIVABLE'
  | 'EXPENSE_ESSENTIAL_RENT'
  | 'EXPENSE_ESSENTIAL_GROCERY'
  | 'EXPENSE_ESSENTIAL_UTILITY'
  | 'EXPENSE_OPERATIONAL_RAW_MATERIAL'
  | 'EXPENSE_OPERATIONAL_PAYROLL'
  | 'EXPENSE_OPERATIONAL_FUEL'
  | 'EXPENSE_DISCRETIONARY'
  | 'DEBT_EMI_LOAN'
  | 'DEBT_CREDIT_CARD'
  | 'STATUTORY_TAX_GST'
  | 'STATUTORY_TDS_EPF';

export interface Transaction {
  id: string;
  customerId: string;
  date: string; // YYYY-MM-DD
  amount: number;
  direction: 'INFLOW' | 'OUTFLOW';
  category: TransactionCategory;
  narration: string;
  channel: 'UPI' | 'NEFT' | 'RTGS' | 'NACH' | 'CARD' | 'CASH';
  metadata?: {
    upiVpa?: string;
    invoiceRef?: string;
    fipSource?: string;
  };
}

export interface Loan {
  id: string;
  customerId: string;
  lenderName: string;
  lenderType: 'SCHEDULED_COMMERCIAL_BANK' | 'SMALL_FINANCE_BANK' | 'NBFC' | 'MFI';
  loanType: 'TERM_LOAN_MACHINERY' | 'WORKING_CAPITAL_CASH_CREDIT' | 'HOME_LOAN' | 'VEHICLE_LOAN' | 'PERSONAL_LOAN' | 'CREDIT_CARD';
  principalAmount: number;
  outstandingPrincipal: number;
  interestRateAnnual: number;
  monthlyEmi: number;
  tenureMonthsRemaining: number;
  nachDebitDate: number; // Day of month (e.g. 5, 10)
  dpd: number; // Days past due
  isAssetBacked: boolean;
  assetRefId?: string;
}

export interface FixedObligation {
  id: string;
  customerId: string;
  category: string;
  amount: number;
  dueDayOfMonth: number;
  isMandatory: boolean;
}

export interface BusinessAsset {
  id: string;
  customerId: string;
  name: string;
  type: 'MACHINE' | 'VEHICLE' | 'EQUIPMENT' | 'PRODUCTION_LINE';
  purchaseCost: number;
  dedicatedLoanId?: string;
  monthlyOperatingCost: number;
  monthlyAttributableRevenue: number;
  utilizationRatePercentage: number;
  status: 'PRODUCTIVE' | 'MARGINAL' | 'LOSS_MAKING' | 'IDLE';
}

export interface IndustryClusterBenchmark {
  clusterId: string;
  industry: string;
  region: string; // e.g., 'Tiruppur', 'Surat', 'Morbi', 'Ludhiana', 'Bengaluru'
  month: number; // 1-12
  averageRevenueIndex: number;
  revenueGrowthPercentageMom: number;
  seasonalVolatilityIndex: number;
  typicalOperatingMargin: number;
}

export interface CustomerProfile {
  id: string;
  name: string;
  archetype: CustomerArchetype;
  occupationOrIndustry: string;
  clusterRegion: string;
  panMasked: string;
  udyamOrEshramNumber?: string;
  accountOpeningDate: string;
  primaryBank: string;
  
  // Consent Tracking
  consent: {
    aaConsentHandle: string;
    status: 'ACTIVE' | 'EXPIRED' | 'REVOKED';
    expiryDate: string;
    dataCompletenessPercentage: number;
  };

  // Financial Reality Snapshot
  financialReality: {
    currentLiquidBalance: number;
    monthlyAverageIncome: number;
    monthlyEssentialExpenses: number;
    totalMonthlyDebtObligation: number;
    totalOutstandingDebt: number;
    cashRunwayDays: number;
    criticalLiquidityDate: string;
    incomeVolatilityRatio: number;
  };

  // Computed Scores
  scores: {
    financialHealthScore: number; // 0-100 (instant solvency)
    contextualDistressScore: number; // 0-100 (abnormal rate of deterioration)
    distressStatus: DistressStatus;
    confidencePercentage: number;
  };

  // Linked Entities
  loans: Loan[];
  obligations: FixedObligation[];
  assets?: BusinessAsset[];
  receivables?: {
    id: string;
    buyerName: string;
    amount: number;
    dueDate: string;
    agingDays: number;
    isTredsEligible: boolean;
  }[];
}
