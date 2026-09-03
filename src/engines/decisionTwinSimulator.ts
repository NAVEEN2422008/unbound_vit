import { CustomerProfile } from '../types/models';
import { FinancialRealityEngine, FinancialRealityMetrics } from './financialRealityEngine';

export type InterventionType =
  | 'NEW_EMERGENCY_LOAN'
  | 'EMI_TENOR_RESTRUCTURING'
  | 'TREDS_INVOICE_DISCOUNTING'
  | 'ASSET_SALE_OR_RESTRUCTURING'
  | 'EXPENSE_TRIM_AND_SAVINGS'
  | 'B2B_REVENUE_MATCH';

export interface SimulatedScenarioResult {
  interventionType: InterventionType;
  title: string;
  description: string;
  projectedLiquidBalance: number;
  projectedMonthlyDebtEmi: number;
  projectedDscr: number;
  projectedFoir: number;
  cashRunwayDays: number;
  harmLevel: 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME';
  isPermissibleUnderGuardrail: boolean;
  guardrailViolationReason?: string;
  projectedHealthScore: number;
  projectedDistressScore: number;
  summaryBenefit: string;
}

/**
 * MODULE 6: Decision Twin Simulator
 * Creates a counterfactual replica of customer finances to test Scenarios A to E.
 */
export class DecisionTwinSimulator {
  public static simulateScenario(
    profile: CustomerProfile,
    intervention: InterventionType,
    params: {
      loanAmountRequested?: number;
      tenorExtensionMonths?: number;
      receivablesDiscountAmount?: number;
      expenseReductionPercentage?: number;
      newMonthlyRevenueEstimated?: number;
    } = {}
  ): SimulatedScenarioResult {
    const baseFre = FinancialRealityEngine.computeFinancialReality(profile);
    
    let liquidBalance = baseFre.currentLiquidBalance;
    let monthlyIncome = profile.financialReality.monthlyAverageIncome;
    let monthlyExpenses = profile.financialReality.monthlyEssentialExpenses;
    let monthlyDebtEmi = baseFre.totalMonthlyDebtEmi;
    let totalDebt = baseFre.totalOutstandingDebt;
    let harmLevel: 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME' = 'LOW';
    let isPermissible = true;
    let violationReason: string | undefined;
    let title = '';
    let description = '';
    let benefit = '';

    // Calculate fixed mandatory statutory obligations (Rent, Payroll, Electricity, Taxes)
    const totalMandatoryObligations = profile.obligations
      .filter(o => o.isMandatory)
      .reduce((s, o) => s + o.amount, 0);

    switch (intervention) {
      case 'NEW_EMERGENCY_LOAN': {
        const loanAmount = params.loanAmountRequested || (profile.archetype === 'MSME' ? 500000 : 50000);
        const interestRate = 0.16; // 16% p.a.
        const tenure = 24; // 24 months
        const monthlyRate = interestRate / 12;
        const newEmi = Math.round(
          (loanAmount * monthlyRate * Math.pow(1 + monthlyRate, tenure)) / (Math.pow(1 + monthlyRate, tenure) - 1)
        );

        liquidBalance += loanAmount;
        monthlyDebtEmi += newEmi;
        totalDebt += loanAmount;

        title = `Option 1: Emergency Working Capital Loan (+₹${loanAmount.toLocaleString('en-IN')})`;
        description = `Disburses ₹${loanAmount.toLocaleString('en-IN')} upfront, but adds ₹${newEmi.toLocaleString('en-IN')}/month in fixed EMI obligations for 24 months.`;
        benefit = `Immediate liquidity injected, extending short-term cash runway.`;
        harmLevel = 'EXTREME';
        break;
      }

      case 'EMI_TENOR_RESTRUCTURING': {
        const extension = params.tenorExtensionMonths || 18;
        const emiReduction = Math.round(monthlyDebtEmi * 0.35);
        monthlyDebtEmi -= emiReduction;

        title = `Option 2: RBI MSME Debt Restructuring (Tenor Extension +${extension}m)`;
        description = `Reschedules principal payments over an extended term, reducing fixed monthly debt outlays by ₹${emiReduction.toLocaleString('en-IN')}/month.`;
        benefit = `Substantially lowers monthly debt service pressure without taking on additional principal.`;
        harmLevel = 'LOW';
        break;
      }

      case 'TREDS_INVOICE_DISCOUNTING': {
        const discountAmount = params.receivablesDiscountAmount || 1200000;
        const tredsFee = Math.round(discountAmount * 0.02); // 2% one-time factoring fee
        const netCashRealized = discountAmount - tredsFee;

        liquidBalance += netCashRealized;

        title = `Option 3: TReDS Receivables Discounting (₹${discountAmount.toLocaleString('en-IN')})`;
        description = `Discounts approved buyer invoices on TReDS (RXIL/Invoicemart) at 8.5% annualized factoring rate, realizing ₹${netCashRealized.toLocaleString('en-IN')} in 48 hours.`;
        benefit = `Converts locked trade receivables into immediate liquidity with zero balance-sheet debt.`;
        harmLevel = 'LOW';
        break;
      }

      case 'ASSET_SALE_OR_RESTRUCTURING': {
        const machineEmiSaved = 65000;
        const operatingCostSaved = 120000;
        monthlyDebtEmi = Math.max(0, monthlyDebtEmi - machineEmiSaved);
        monthlyExpenses = Math.max(0, monthlyExpenses - operatingCostSaved);

        title = `Option 4: Targeted Machine C Loan Restructuring & Capacity Subleasing`;
        description = `Restructures dedicated machinery loan terms and leases out idle capacity, eliminating -₹85,000/month in operating losses.`;
        benefit = `Eliminates the primary financial drain on enterprise cash flow.`;
        harmLevel = 'LOW';
        break;
      }

      case 'EXPENSE_TRIM_AND_SAVINGS': {
        const trimPercentage = params.expenseReductionPercentage || 15;
        const savings = Math.round(monthlyExpenses * (trimPercentage / 100));
        monthlyExpenses -= savings;

        title = `Option 5: Operational & Discretionary Expense Optimization (-${trimPercentage}%)`;
        description = `Trims non-essential overheads and non-mandatory discretionary spending, conserving ₹${savings.toLocaleString('en-IN')}/month.`;
        benefit = `Expands monthly cash buffer without external financing.`;
        harmLevel = 'LOW';
        break;
      }

      case 'B2B_REVENUE_MATCH': {
        const addedRevenue = params.newMonthlyRevenueEstimated || 450000;
        monthlyIncome += addedRevenue;

        title = `Option 6: B2B Business Recovery Network (ONDC Buyer Match)`;
        description = `Matches excess manufacturing capacity with vetted corporate buyer orders, adding ~₹${addedRevenue.toLocaleString('en-IN')}/month in high-margin sales.`;
        benefit = `Solves the root order deficit directly through commercial demand generation.`;
        harmLevel = 'LOW';
        break;
      }
    }

    // Compute updated financial ratios
    // Total operational overheads = essential living/manufacturing expenses + fixed mandatory bills (Rent/Wages/Power/Taxes)
    const totalOperatingOutflows = monthlyExpenses + totalMandatoryObligations;
    const netOperatingIncome = monthlyIncome - totalOperatingOutflows;
    
    // DSCR = Net Operating Income / Total Debt Service (Monthly Debt EMI)
    const projectedDscr = monthlyDebtEmi > 0 ? Number((netOperatingIncome / monthlyDebtEmi).toFixed(2)) : 3.0;
    const projectedFoir = monthlyIncome > 0 ? Number(((monthlyDebtEmi + totalMandatoryObligations) / monthlyIncome).toFixed(3)) : 1.0;

    // Daily burn and runway
    const totalOutflows = monthlyDebtEmi + totalOperatingOutflows;
    const dailyBurn = totalOutflows > 0 ? totalOutflows / 30 : 1;
    const cashRunwayDays = Math.max(0, Math.round(liquidBalance / dailyBurn));

    // Hard Safety Guardrail Check
    if (intervention === 'NEW_EMERGENCY_LOAN') {
      if (projectedDscr < 1.25 || projectedFoir > 0.60) {
        isPermissible = false;
        violationReason = `Debt Service Coverage Ratio (DSCR) is ${projectedDscr} (strictly below mandatory RBI threshold of 1.25) and FOIR is ${(projectedFoir * 100).toFixed(1)}%. Adding more debt precipitates insolvency.`;
        harmLevel = 'EXTREME';
      }
    }

    // Score projections
    let projectedHealth = baseFre.financialHealthScore;
    let projectedDistress = 75;

    if (intervention === 'NEW_EMERGENCY_LOAN') {
      projectedHealth = isPermissible ? projectedHealth + 5 : Math.max(15, projectedHealth - 25);
      projectedDistress = isPermissible ? 60 : 92;
    } else {
      projectedHealth = Math.min(100, projectedHealth + 25);
      projectedDistress = Math.max(15, 30);
    }

    return {
      interventionType: intervention,
      title,
      description,
      projectedLiquidBalance: liquidBalance,
      projectedMonthlyDebtEmi: monthlyDebtEmi,
      projectedDscr,
      projectedFoir,
      cashRunwayDays,
      harmLevel,
      isPermissibleUnderGuardrail: isPermissible,
      guardrailViolationReason: violationReason,
      projectedHealthScore: projectedHealth,
      projectedDistressScore: projectedDistress,
      summaryBenefit: benefit
    };
  }
}
