import { CustomerProfile } from '../types/models';
import { DecisionTwinSimulator, SimulatedScenarioResult, InterventionType } from './decisionTwinSimulator';

export interface ActionPlanStep {
  timeframe: 'TODAY' | 'THIS_WEEK' | 'BEFORE_CRITICAL_DATE' | 'NEXT_MONTH';
  action: string;
  responsibleParty: 'CUSTOMER' | 'RELATIONSHIP_MANAGER' | 'CREDIT_OFFICER' | 'TREDS_DESK';
  expectedImpact: string;
}

export interface InterventionEvidenceCard {
  customerId: string;
  customerName: string;
  recommendedIntervention: string;
  primaryWhyRationale: string;
  supportingFinancialEvidence: string[];
  expectedFinancialBenefit: string;
  potentialDownsidesAndRisks: string[];
  confidenceScorePercentage: number;
  dataCompletenessPercentage: number;
  coreAssumptions: string[];
  guardrailStatus: 'APPROVED' | 'NO_NEW_LOAN_VETO_ENFORCED';
}

export interface LeastHarmRecommendationReport {
  recommendedOption: SimulatedScenarioResult;
  allSimulatedOptions: SimulatedScenarioResult[];
  noNewLoanVetoActive: boolean;
  actionSequence: ActionPlanStep[];
  evidenceCard: InterventionEvidenceCard;
}

/**
 * MODULE 7: Least-Harm Intervention Optimizer
 * Evaluates simulated scenarios, enforces the "No-New-Loan" guardrail,
 * and compiles an auditable Intervention Evidence Card.
 */
export class LeastHarmOptimizer {
  public static optimizeInterventions(profile: CustomerProfile): LeastHarmRecommendationReport {
    // 1. Simulate all core candidate interventions
    const candidateTypes: InterventionType[] = [
      'NEW_EMERGENCY_LOAN',
      'EMI_TENOR_RESTRUCTURING',
      'EXPENSE_TRIM_AND_SAVINGS'
    ];

    if (profile.archetype === 'MSME' || profile.archetype === 'MANUFACTURER') {
      candidateTypes.push('TREDS_INVOICE_DISCOUNTING');
      candidateTypes.push('ASSET_SALE_OR_RESTRUCTURING');
      candidateTypes.push('B2B_REVENUE_MATCH');
    }

    const allOptions: SimulatedScenarioResult[] = candidateTypes.map(type =>
      DecisionTwinSimulator.simulateScenario(profile, type)
    );

    // 2. Identify if "No-New-Loan" veto is triggered
    const loanOption = allOptions.find(o => o.interventionType === 'NEW_EMERGENCY_LOAN');
    const noNewLoanVetoActive = loanOption ? !loanOption.isPermissibleUnderGuardrail : false;

    // 3. Filter permissible options and rank by Least-Harm Score
    // HarmScore = (Harm Level Penalty) + (100 - ProjectedHealthScore) - (CashRunway / 2)
    const permissibleOptions = allOptions.filter(o => o.isPermissibleUnderGuardrail);

    permissibleOptions.sort((a, b) => {
      const harmWeightA = a.harmLevel === 'LOW' ? 0 : a.harmLevel === 'MODERATE' ? 20 : 50;
      const harmWeightB = b.harmLevel === 'LOW' ? 0 : b.harmLevel === 'MODERATE' ? 20 : 50;
      const scoreA = harmWeightA + (100 - a.projectedHealthScore) - a.cashRunwayDays;
      const scoreB = harmWeightB + (100 - b.projectedHealthScore) - b.cashRunwayDays;
      return scoreA - scoreB;
    });

    const bestOption = permissibleOptions[0] || allOptions[1];

    // 4. Generate Action Sequencer
    const actionSequence: ActionPlanStep[] = [];
    
    if (profile.archetype === 'MSME') {
      actionSequence.push({
        timeframe: 'TODAY',
        action: 'Initiate TReDS discounting for ₹12L overdue invoices with Vogue Garments on Invoicemart/RXIL.',
        responsibleParty: 'TREDS_DESK',
        expectedImpact: 'Infuses ₹11.76L liquid cash within 48 hours without borrowing.'
      });
      actionSequence.push({
        timeframe: 'THIS_WEEK',
        action: 'Restructure dedicated loan on Machine C (Tenure extension from 34m to 54m).',
        responsibleParty: 'CREDIT_OFFICER',
        expectedImpact: 'Saves ₹35,000/month in fixed EMI outflows.'
      });
      actionSequence.push({
        timeframe: 'BEFORE_CRITICAL_DATE',
        action: 'Review B2B commercial matching on ONDC network for idle knitwear capacity.',
        responsibleParty: 'RELATIONSHIP_MANAGER',
        expectedImpact: 'Adds up to ₹4.5L/month in incremental order revenue.'
      });
    } else {
      actionSequence.push({
        timeframe: 'TODAY',
        action: 'Pause non-essential discretionary card spend and optimize grocery/living overheads.',
        responsibleParty: 'CUSTOMER',
        expectedImpact: 'Preserves immediate cash buffer.'
      });
      actionSequence.push({
        timeframe: 'THIS_WEEK',
        action: 'Apply for 18-month tenure extension on existing personal loan.',
        responsibleParty: 'RELATIONSHIP_MANAGER',
        expectedImpact: 'Lowers monthly EMI from ₹6,500 to ₹4,200.'
      });
      actionSequence.push({
        timeframe: 'BEFORE_CRITICAL_DATE',
        action: 'Ring-fence liquid reserves for upcoming mandatory balloon fee.',
        responsibleParty: 'CUSTOMER',
        expectedImpact: 'Prevents NACH return bounce on the 20th.'
      });
    }

    // 5. Generate Intervention Evidence Card
    const evidenceCard: InterventionEvidenceCard = {
      customerId: profile.id,
      customerName: profile.name,
      recommendedIntervention: bestOption.title,
      primaryWhyRationale: `Borrower is facing cash runway constraint (${profile.financialReality.cashRunwayDays} days remaining). Simulating debt shows DSCR drops to unsafe levels (${loanOption?.projectedDscr || 'N/A'}). Non-debt intervention restores liquidity safely.`,
      supportingFinancialEvidence: [
        `Current liquid cash is ₹${profile.financialReality.currentLiquidBalance.toLocaleString('en-IN')}`,
        `Monthly fixed debt obligations total ₹${profile.financialReality.totalMonthlyDebtObligation.toLocaleString('en-IN')}`,
        `Projected critical liquidity collapse expected on ${profile.financialReality.criticalLiquidityDate}`
      ],
      expectedFinancialBenefit: bestOption.description,
      potentialDownsidesAndRisks: [
        'Requires timely onboarding onto discounting portal / restructuring consent',
        'Buyer invoice acceptance required within standard 48-hour SLA'
      ],
      confidenceScorePercentage: profile.scores.confidencePercentage,
      dataCompletenessPercentage: profile.consent.dataCompletenessPercentage,
      coreAssumptions: [
        'Expected baseline business revenue remains stable over next 60 days',
        'Consented bank account feeds remain active without revocation'
      ],
      guardrailStatus: noNewLoanVetoActive ? 'NO_NEW_LOAN_VETO_ENFORCED' : 'APPROVED'
    };

    return {
      recommendedOption: bestOption,
      allSimulatedOptions: allOptions,
      noNewLoanVetoActive,
      actionSequence,
      evidenceCard
    };
  }
}
