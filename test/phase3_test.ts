import { generateCoreScenarios } from '../src/data/generator';
import { DecisionTwinSimulator } from '../src/engines/decisionTwinSimulator';
import { LeastHarmOptimizer } from '../src/engines/leastHarmOptimizer';
import { BusinessRecoveryNetwork } from '../src/engines/businessRecoveryNetwork';

/**
 * FINRES Phase 3 Test & Verification Suite
 * Verifies Decision Twin Counterfactual Simulations, "No-New-Loan" Hard Guardrail,
 * Least-Harm Optimizations, Evidence Cards, and B2B Recovery Network.
 */
function runPhase3Tests() {
  console.log('====================================================');
  console.log(' FINRES PHASE 3: DECISION TWIN & LEAST-HARM ENGINE ');
  console.log('====================================================\n');

  let passed = 0;
  let total = 0;

  function assert(condition: boolean, msg: string) {
    total++;
    if (condition) {
      console.log(`✅ [PASS] ${msg}`);
      passed++;
    } else {
      console.error(`❌ [FAIL] ${msg}`);
    }
  }

  const scenarios = generateCoreScenarios();
  const msme = scenarios.find(s => s.id === 'CUST_MSME_TIRUPPUR_001')!;

  // ----------------------------------------------------
  // Test 1: Decision Twin Simulation - Option 1 (Emergency Loan)
  // ----------------------------------------------------
  const loanSim = DecisionTwinSimulator.simulateScenario(msme, 'NEW_EMERGENCY_LOAN', { loanAmountRequested: 500000 });
  assert(!!loanSim, 'Decision Twin simulated Option 1 (New Loan)');
  assert(loanSim.harmLevel === 'EXTREME', 'Decision Twin flagged ₹5L Emergency Loan with EXTREME harm level');
  assert(loanSim.isPermissibleUnderGuardrail === false, 'Hard "No-New-Loan" Guardrail strictly VETOED the loan');
  assert(loanSim.projectedDscr < 1.25, 'Guardrail correctly proved DSCR drops below mandatory 1.25 threshold');

  // ----------------------------------------------------
  // Test 2: Decision Twin Simulation - Option 3 (TReDS Discounting)
  // ----------------------------------------------------
  const tredsSim = DecisionTwinSimulator.simulateScenario(msme, 'TREDS_INVOICE_DISCOUNTING', { receivablesDiscountAmount: 1200000 });
  assert(tredsSim.isPermissibleUnderGuardrail === true, 'TReDS Discounting is approved as fully permissible');
  assert(tredsSim.harmLevel === 'LOW', 'TReDS Discounting carries LOW harm level');
  assert(tredsSim.projectedLiquidBalance > 1200000, 'TReDS Discounting injected +₹11.76L liquid cash without adding debt');

  // ----------------------------------------------------
  // Test 3: Least-Harm Optimizer & Action Sequencer
  // ----------------------------------------------------
  const optimization = LeastHarmOptimizer.optimizeInterventions(msme);
  assert(optimization.noNewLoanVetoActive === true, 'Least-Harm Optimizer registered active "No-New-Loan" veto');
  assert(optimization.recommendedOption.harmLevel === 'LOW', 'Recommended strategy has LOW harm score');
  assert(optimization.actionSequence.length === 3, 'Action Sequencer generated 3-step prioritized timeline (Today -> This Week -> Before Critical Date)');

  // ----------------------------------------------------
  // Test 4: Intervention Evidence Card
  // ----------------------------------------------------
  const card = optimization.evidenceCard;
  assert(card.guardrailStatus === 'NO_NEW_LOAN_VETO_ENFORCED', 'Evidence Card explicitly marks NO_NEW_LOAN_VETO_ENFORCED');
  assert(card.supportingFinancialEvidence.length >= 3, 'Evidence Card contains 3+ concrete financial signals');
  assert(card.confidenceScorePercentage >= 90, 'Evidence Card confidence score exceeds 90%');

  // ----------------------------------------------------
  // Test 5: B2B Business Recovery Network (ONDC Interoperability)
  // ----------------------------------------------------
  const opportunities = BusinessRecoveryNetwork.findOpportunitiesForSupplier(msme.id);
  assert(opportunities.length >= 2, 'B2B Network discovered 2 commercial corporate buyer matches');
  assert(opportunities[0].compatibilityScorePercentage >= 88, 'Matching compatibility score exceeds 88%');
  assert(opportunities[0].privacyStatus === 'DOUBLE_BLIND_LOCKED', 'Initial matching strictly maintains DOUBLE_BLIND_LOCKED privacy');

  const consented = BusinessRecoveryNetwork.grantConsent(opportunities[0].matchId, 'SUPPLIER');
  assert(consented?.privacyStatus === 'SUPPLIER_CONSENTED', 'Supplier consent safely logged in audit ledger');

  console.log('\n----------------------------------------------------');
  console.log(`Phase 3 Result: ${passed}/${total} tests passed.`);
  if (passed === total) {
    console.log('🎉 PHASE 3 DECISION TWIN & LEAST-HARM ENGINE FULLY VERIFIED!');
  } else {
    console.error('⚠️ SOME PHASE 3 TESTS FAILED.');
    process.exit(1);
  }
}

runPhase3Tests();
