import { CustomerProfile, Loan, FixedObligation } from '../types/models';

export interface FinancialRealityMetrics {
  currentLiquidBalance: number;
  totalMonthlyDebtEmi: number;
  totalOutstandingDebt: number;
  monthlyEssentialExpenseBurden: number;
  netMonthlyCashFlow: number;
  debtToIncomeRatio: number;
  fixedObligationToIncomeRatio: number; // FOIR
  cashRunwayDays: number;
  dataCompletenessPercentage: number;
  financialHealthScore: number; // 0 - 100
  summaryExplanation: string;
}

/**
 * MODULE 2: Financial Reality Engine (FRE)
 * Unifies multi-lender debt, calculates true liquidity runway, and scores balance sheet solvency.
 */
export class FinancialRealityEngine {
  public static computeFinancialReality(
    profile: CustomerProfile,
    simulatedMonthlyIncome?: number,
    simulatedMonthlyExpenses?: number
  ): FinancialRealityMetrics {
    const income = simulatedMonthlyIncome !== undefined ? simulatedMonthlyIncome : profile.financialReality.monthlyAverageIncome;
    const essentialExpenses = simulatedMonthlyExpenses !== undefined ? simulatedMonthlyExpenses : profile.financialReality.monthlyEssentialExpenses;
    
    // 1. Calculate multi-lender debt obligations
    const totalMonthlyDebtEmi = profile.loans.reduce((sum, l) => sum + l.monthlyEmi, 0);
    const totalOutstandingDebt = profile.loans.reduce((sum, l) => sum + l.outstandingPrincipal, 0);

    // 2. Fixed mandatory obligations (Rent, Payroll, Electricity, Taxes)
    const totalMandatoryObligations = profile.obligations
      .filter(o => o.isMandatory)
      .reduce((sum, o) => sum + o.amount, 0);

    const totalOutflows = totalMonthlyDebtEmi + essentialExpenses;
    const netMonthlyCashFlow = income - totalOutflows;

    // 3. Financial Ratios
    const debtToIncomeRatio = income > 0 ? Number((totalMonthlyDebtEmi / income).toFixed(3)) : 1.0;
    const fixedObligationToIncomeRatio = income > 0 ? Number(((totalMonthlyDebtEmi + totalMandatoryObligations) / income).toFixed(3)) : 1.0;

    // 4. Cash Runway Calculation
    const dailyEssentialBurn = totalOutflows > 0 ? totalOutflows / 30 : 1;
    const cashRunwayDays = Math.max(0, Math.round(profile.financialReality.currentLiquidBalance / dailyEssentialBurn));

    // 5. Data Completeness & Epistemic Confidence
    const dataCompletenessPercentage = profile.consent.dataCompletenessPercentage;

    // 6. Solvency / Financial Health Score (0 - 100)
    let healthScore = 50;
    if (netMonthlyCashFlow > 0) healthScore += 15;
    else healthScore -= 20;

    if (debtToIncomeRatio < 0.35) healthScore += 20;
    else if (debtToIncomeRatio > 0.55) healthScore -= 25;

    if (cashRunwayDays > 45) healthScore += 15;
    else if (cashRunwayDays < 15) healthScore -= 20;

    healthScore = Math.min(100, Math.max(0, Math.round(healthScore)));

    const summaryExplanation = `Monthly Income is ₹${income.toLocaleString('en-IN')}, with total debt EMI of ₹${totalMonthlyDebtEmi.toLocaleString('en-IN')} across ${profile.loans.length} lenders. Liquid reserves cover approximately ${cashRunwayDays} days of essential commitments.`;

    return {
      currentLiquidBalance: profile.financialReality.currentLiquidBalance,
      totalMonthlyDebtEmi,
      totalOutstandingDebt,
      monthlyEssentialExpenseBurden: essentialExpenses,
      netMonthlyCashFlow,
      debtToIncomeRatio,
      fixedObligationToIncomeRatio,
      cashRunwayDays,
      dataCompletenessPercentage,
      financialHealthScore: healthScore,
      summaryExplanation
    };
  }
}
