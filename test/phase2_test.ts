import { generateCoreScenarios } from '../src/data/generator';
import { FinresDiagnosticCoordinator } from '../src/engines/coordinator';

/**
 * FINRES Phase 2 Test & Verification Suite
 */
function runPhase2Tests() {
  console.log('====================================================');
  console.log('   FINRES PHASE 2: CORE INTELLIGENCE ENGINES TEST   ');
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

  // ----------------------------------------------------
  // Test 1: MSME Scenario (Sri Balaji Fabrics, Tiruppur)
  // ----------------------------------------------------
  const msme = scenarios.find(s => s.id === 'CUST_MSME_TIRUPPUR_001')!;
  const msmeReport = FinresDiagnosticCoordinator.diagnoseCustomer(msme, -24.0, 9);

  assert(!!msmeReport, 'MSME diagnostic report generated');
  assert(msmeReport.financialReality.totalMonthlyDebtEmi === 320000, 'FRE correctly consolidated multi-lender debt to ₹3,20,000/mo');
  assert(msmeReport.contextIntelligence.contextualDistressScore >= 80, 'CIE flagged structural deterioration (Contextual Distress Score >= 80) due to 19% underperformance vs Tiruppur cluster');
  assert(msmeReport.collisionRadar.criticalLiquidityDate !== null, 'OCR identified upcoming liquidity collision date');
  assert(msmeReport.assetDiagnostic.lossMakingAssetsCount === 1, 'ALE isolated exactly 1 loss-making asset (Machine C)');
  
  const machineC = msmeReport.assetDiagnostic.assetBreakdown.find(a => a.assetId === 'ASSET_MACH_C');
  assert(machineC?.netMonthlyContribution === -85000, 'ALE calculated Machine C exact net bleed of -₹85,000/month');

  // ----------------------------------------------------
  // Test 2: Salaried Scenario (Ananya Sharma, Bengaluru)
  // ----------------------------------------------------
  const salaried = scenarios.find(s => s.id === 'CUST_SALARIED_BLR_002')!;
  const salariedReport = FinresDiagnosticCoordinator.diagnoseCustomer(salaried, -2.0, 9);

  assert(!!salariedReport, 'Salaried diagnostic report generated');
  assert(salariedReport.collisionRadar.criticalLiquidityDate !== null, 'OCR correctly forecasted balloon school fee collision');
  assert(salariedReport.collisionRadar.maximumProjectedShortfall >= 15000, 'OCR identified projected shortfall > ₹15,000 when balloon fee arrives');

  // ----------------------------------------------------
  // Test 3: Seasonal Decoupling Validation
  // ----------------------------------------------------
  // In January, Tiruppur cluster averages -22.0% due to seasonal export lull.
  // If a business is down 22.0%, CIE MUST classify it as a benign seasonal dip.
  const msmeSeasonalReport = FinresDiagnosticCoordinator.diagnoseCustomer(msme, -22.0, 1);
  assert(msmeSeasonalReport.contextIntelligence.isSeasonalDip === true, 'CIE correctly identified benign Seasonal Dip when business dip mirrors cluster dip');
  assert(msmeSeasonalReport.contextIntelligence.contextualDistressScore < 50, 'CIE assigned low distress score (<50) for normal seasonal dip, preventing false alarm');

  console.log('\n----------------------------------------------------');
  console.log(`Phase 2 Result: ${passed}/${total} tests passed.`);
  if (passed === total) {
    console.log('🎉 PHASE 2 CORE ENGINES VERIFIED SUCCESSFULLY!');
  } else {
    console.error('⚠️ SOME PHASE 2 TESTS FAILED.');
    process.exit(1);
  }
}

runPhase2Tests();
