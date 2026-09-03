import { generateCoreScenarios, generateSyntheticClusterBenchmarks, generateBulkProfiles, saveAllDataToDisk } from '../src/data/generator';
import * as path from 'path';
import * as fs from 'fs';

/**
 * FINRES Phase 1 Validation & Unit Test Suite
 */
function runPhase1Tests() {
  console.log('====================================================');
  console.log('       FINRES PHASE 1: DATA MODEL & GENERATOR TEST   ');
  console.log('====================================================\n');

  let testsPassed = 0;
  let totalTests = 0;

  function assert(condition: boolean, testName: string) {
    totalTests++;
    if (condition) {
      console.log(`✅ [PASS] ${testName}`);
      testsPassed++;
    } else {
      console.error(`❌ [FAIL] ${testName}`);
    }
  }

  // Test 1: Generate Core Scenarios
  const coreScenarios = generateCoreScenarios();
  assert(coreScenarios.length === 3, 'Core scenarios generated exactly 3 distinct archetypes');

  // Test 2: Verify MSME Scenario 1 Properties
  const msme = coreScenarios.find(s => s.id === 'CUST_MSME_TIRUPPUR_001');
  assert(!!msme, 'MSME Tiruppur scenario exists');
  assert(msme?.archetype === 'MSME', 'MSME archetype correctly typed');
  assert(msme?.assets?.length === 3, 'MSME has 3 distinct physical assets/machines');
  
  const lossMachine = msme?.assets?.find(a => a.id === 'ASSET_MACH_C');
  assert(lossMachine?.status === 'LOSS_MAKING', 'Machine C correctly flagged as LOSS_MAKING asset');
  assert((msme?.receivables?.length || 0) > 0, 'MSME has overdue TReDS-eligible receivables');

  // Test 3: Verify Salaried Scenario 2 Balloon Fee
  const salaried = coreScenarios.find(s => s.id === 'CUST_SALARIED_BLR_002');
  assert(!!salaried, 'Salaried Bengaluru scenario exists');
  const balloonObligation = salaried?.obligations.find(o => o.id === 'OBL_BALLOON_FEE');
  assert(!!balloonObligation && balloonObligation.amount === 42000, 'Salaried profile contains upcoming ₹42,000 balloon school fee obligation');

  // Test 4: Verify Gig Worker Scenario 3
  const gig = coreScenarios.find(s => s.id === 'CUST_GIG_BLR_003');
  assert(!!gig, 'Gig worker scenario exists');
  assert(gig?.archetype === 'GIG_WORKER', 'Gig worker archetype correctly typed');
  assert((gig?.financialReality.incomeVolatilityRatio || 0) > 0.35, 'Gig worker reflects high income volatility ratio (>0.35)');

  // Test 5: Verify Cluster Benchmarks
  const benchmarks = generateSyntheticClusterBenchmarks();
  assert(benchmarks.length === 6 * 12, 'Cluster benchmarks cover 6 Indian clusters across 12 calendar months (72 total records)');
  const tiruppurJan = benchmarks.find(b => b.region === 'Tiruppur' && b.month === 1);
  assert(!!tiruppurJan && tiruppurJan.averageRevenueIndex < 100, 'Tiruppur reflects post-holiday seasonal export lull in January');

  // Test 6: Bulk Generation
  const bulk = generateBulkProfiles(100);
  assert(bulk.length === 100, 'Bulk generator produced 100 diverse customer profiles');
  const uniqueArchetypes = new Set(bulk.map(b => b.archetype));
  assert(uniqueArchetypes.size >= 8, 'Bulk profiles cover wide range of customer archetypes');

  // Test 7: File Persistence
  const testDataDir = path.join(__dirname, '../data');
  saveAllDataToDisk(testDataDir);
  assert(fs.existsSync(path.join(testDataDir, 'profiles.json')), 'profiles.json successfully persisted to disk');
  assert(fs.existsSync(path.join(testDataDir, 'benchmarks.json')), 'benchmarks.json successfully persisted to disk');

  console.log('\n----------------------------------------------------');
  console.log(`Result: ${testsPassed}/${totalTests} tests passed.`);
  if (testsPassed === totalTests) {
    console.log('🎉 PHASE 1 VERIFICATION COMPLETED SUCCESSFULLY!');
  } else {
    console.error('⚠️ SOME PHASE 1 TESTS FAILED.');
    process.exit(1);
  }
}

runPhase1Tests();
