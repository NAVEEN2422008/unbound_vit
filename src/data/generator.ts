import { CustomerProfile, Transaction, IndustryClusterBenchmark, CustomerArchetype, DistressStatus } from '../types/models';
import * as fs from 'fs';
import * as path from 'path';

/**
 * FINRES High-Fidelity Synthetic Data Generator
 * Generates realistic profiles and time-series transactions across all 11 archetypes.
 */

const CLUSTERS = [
  { region: 'Tiruppur', industry: 'Textiles & Knitwear', state: 'Tamil Nadu' },
  { region: 'Surat', industry: 'Synthetic Textiles & Diamonds', state: 'Gujarat' },
  { region: 'Morbi', industry: 'Ceramics & Tiles', state: 'Gujarat' },
  { region: 'Ludhiana', industry: 'Engineering & Bicycle Parts', state: 'Punjab' },
  { region: 'Bengaluru', industry: 'IT Services & Gig Economy', state: 'Karnataka' },
  { region: 'Mumbai', industry: 'Financial Services & Retail', state: 'Maharashtra' },
];

export function generateSyntheticClusterBenchmarks(): IndustryClusterBenchmark[] {
  const benchmarks: IndustryClusterBenchmark[] = [];
  
  CLUSTERS.forEach((cl, idx) => {
    for (let month = 1; month <= 12; month++) {
      // Create seasonal patterns (e.g., monsoon dip in months 6-8, post-festive dip in months 1-2)
      let seasonalFactor = 1.0;
      if (cl.region === 'Tiruppur' && (month === 1 || month === 2)) seasonalFactor = 0.78; // Post-Christmas export lull
      if (cl.region === 'Morbi' && (month === 7 || month === 8)) seasonalFactor = 0.82; // Monsoon slowdown
      if (cl.region === 'Surat' && (month === 10 || month === 11)) seasonalFactor = 1.35; // Diwali surge

      benchmarks.push({
        clusterId: `CLUST_${idx + 1}`,
        industry: cl.industry,
        region: cl.region,
        month,
        averageRevenueIndex: Math.round(100 * seasonalFactor),
        revenueGrowthPercentageMom: Number(((seasonalFactor - 1) * 15).toFixed(1)),
        seasonalVolatilityIndex: 0.18,
        typicalOperatingMargin: 0.22,
      });
    }
  });

  return benchmarks;
}

export function generateCoreScenarios(): CustomerProfile[] {
  const profiles: CustomerProfile[] = [];

  // 1. MUST-HAVE SCENARIO 1: MSME Textile Manufacturer with loss-making Machine C and delayed receivables
  profiles.push({
    id: 'CUST_MSME_TIRUPPUR_001',
    name: 'Sri Balaji Fabrics & Knits Pvt Ltd',
    archetype: 'MSME',
    occupationOrIndustry: 'Textiles & Knitwear',
    clusterRegion: 'Tiruppur',
    panMasked: 'AAACB1234F',
    udyamOrEshramNumber: 'UDYAM-TN-28-0019284',
    accountOpeningDate: '2021-04-10',
    primaryBank: 'State Bank of India',
    consent: {
      aaConsentHandle: 'CONSENT_AA_9821_771',
      status: 'ACTIVE',
      expiryDate: '2027-04-10',
      dataCompletenessPercentage: 94,
    },
    financialReality: {
      currentLiquidBalance: 140000,
      monthlyAverageIncome: 2800000,
      monthlyEssentialExpenses: 2350000,
      totalMonthlyDebtObligation: 320000,
      totalOutstandingDebt: 3800000,
      cashRunwayDays: 19,
      criticalLiquidityDate: '2026-09-24',
      incomeVolatilityRatio: 0.28,
    },
    scores: {
      financialHealthScore: 58,
      contextualDistressScore: 84, // Down 24% when cluster is down only 5%
      distressStatus: 'VULNERABLE',
      confidencePercentage: 91,
    },
    loans: [
      {
        id: 'LOAN_TERM_01',
        customerId: 'CUST_MSME_TIRUPPUR_001',
        lenderName: 'State Bank of India',
        lenderType: 'SCHEDULED_COMMERCIAL_BANK',
        loanType: 'TERM_LOAN_MACHINERY',
        principalAmount: 2500000,
        outstandingPrincipal: 1800000,
        interestRateAnnual: 11.5,
        monthlyEmi: 65000,
        tenureMonthsRemaining: 34,
        nachDebitDate: 10,
        dpd: 0,
        isAssetBacked: true,
        assetRefId: 'ASSET_MACH_C',
      },
      {
        id: 'LOAN_CC_01',
        customerId: 'CUST_MSME_TIRUPPUR_001',
        lenderName: 'Canara Bank',
        lenderType: 'SCHEDULED_COMMERCIAL_BANK',
        loanType: 'WORKING_CAPITAL_CASH_CREDIT',
        principalAmount: 2000000,
        outstandingPrincipal: 1950000,
        interestRateAnnual: 12.0,
        monthlyEmi: 255000, // Includes interest & CC service
        tenureMonthsRemaining: 12,
        nachDebitDate: 24,
        dpd: 0,
        isAssetBacked: false,
      }
    ],
    obligations: [
      { id: 'OBL_RENT', customerId: 'CUST_MSME_TIRUPPUR_001', category: 'Factory Shed Rent', amount: 150000, dueDayOfMonth: 5, isMandatory: true },
      { id: 'OBL_PAYROLL', customerId: 'CUST_MSME_TIRUPPUR_001', category: 'Worker Wages', amount: 750000, dueDayOfMonth: 7, isMandatory: true },
      { id: 'OBL_POWER', customerId: 'CUST_MSME_TIRUPPUR_001', category: 'TANGEDCO Electricity', amount: 220000, dueDayOfMonth: 15, isMandatory: true },
      { id: 'OBL_GST', customerId: 'CUST_MSME_TIRUPPUR_001', category: 'GSTR-3B Tax Liability', amount: 180000, dueDayOfMonth: 20, isMandatory: true },
    ],
    assets: [
      {
        id: 'ASSET_MACH_A',
        customerId: 'CUST_MSME_TIRUPPUR_001',
        name: 'High-Speed Circular Knitting Machine 1',
        type: 'MACHINE',
        purchaseCost: 2000000,
        monthlyOperatingCost: 350000,
        monthlyAttributableRevenue: 600000,
        utilizationRatePercentage: 88,
        status: 'PRODUCTIVE',
      },
      {
        id: 'ASSET_MACH_B',
        customerId: 'CUST_MSME_TIRUPPUR_001',
        name: 'Circular Knitting Machine 2',
        type: 'MACHINE',
        purchaseCost: 1800000,
        monthlyOperatingCost: 300000,
        monthlyAttributableRevenue: 420000,
        utilizationRatePercentage: 75,
        status: 'PRODUCTIVE',
      },
      {
        id: 'ASSET_MACH_C',
        customerId: 'CUST_MSME_TIRUPPUR_001',
        name: 'Specialty Dyeing & Finishing Unit (Machine C)',
        type: 'MACHINE',
        purchaseCost: 2500000,
        dedicatedLoanId: 'LOAN_TERM_01',
        monthlyOperatingCost: 210000,
        monthlyAttributableRevenue: 190000, // Revenue 190k - OpCost 210k - EMI 65k = -85k cash bleed!
        utilizationRatePercentage: 30,
        status: 'LOSS_MAKING',
      }
    ],
    receivables: [
      { id: 'REC_01', buyerName: 'Vogue Garments Retailers (Mumbai)', amount: 1200000, dueDate: '2026-08-15', agingDays: 45, isTredsEligible: true },
      { id: 'REC_02', buyerName: 'Chennai Cotton Traders', amount: 450000, dueDate: '2026-09-01', agingDays: 28, isTredsEligible: true },
    ]
  });

  // 2. MUST-HAVE SCENARIO 2: Salaried Individual with sudden upcoming balloon education fee collision
  profiles.push({
    id: 'CUST_SALARIED_BLR_002',
    name: 'Ananya Sharma',
    archetype: 'SALARIED',
    occupationOrIndustry: 'Senior QA Engineer (IT Services)',
    clusterRegion: 'Bengaluru',
    panMasked: 'BKPPS9921D',
    accountOpeningDate: '2022-08-15',
    primaryBank: 'HDFC Bank',
    consent: {
      aaConsentHandle: 'CONSENT_AA_6612_443',
      status: 'ACTIVE',
      expiryDate: '2027-08-15',
      dataCompletenessPercentage: 98,
    },
    financialReality: {
      currentLiquidBalance: 24000,
      monthlyAverageIncome: 55000,
      monthlyEssentialExpenses: 34000,
      totalMonthlyDebtObligation: 11000,
      totalOutstandingDebt: 320000,
      cashRunwayDays: 16,
      criticalLiquidityDate: '2026-09-20',
      incomeVolatilityRatio: 0.04,
    },
    scores: {
      financialHealthScore: 64,
      contextualDistressScore: 78,
      distressStatus: 'VULNERABLE',
      confidencePercentage: 95,
    },
    loans: [
      {
        id: 'LOAN_PERS_01',
        customerId: 'CUST_SALARIED_BLR_002',
        lenderName: 'HDFC Bank',
        lenderType: 'SCHEDULED_COMMERCIAL_BANK',
        loanType: 'PERSONAL_LOAN',
        principalAmount: 200000,
        outstandingPrincipal: 140000,
        interestRateAnnual: 13.5,
        monthlyEmi: 6500,
        tenureMonthsRemaining: 26,
        nachDebitDate: 5,
        dpd: 0,
        isAssetBacked: false,
      },
      {
        id: 'LOAN_CC_02',
        customerId: 'CUST_SALARIED_BLR_002',
        lenderName: 'ICICI Bank',
        lenderType: 'SCHEDULED_COMMERCIAL_BANK',
        loanType: 'CREDIT_CARD',
        principalAmount: 80000,
        outstandingPrincipal: 45000,
        interestRateAnnual: 36.0,
        monthlyEmi: 4500,
        tenureMonthsRemaining: 12,
        nachDebitDate: 12,
        dpd: 0,
        isAssetBacked: false,
      }
    ],
    obligations: [
      { id: 'OBL_RENT_BLR', customerId: 'CUST_SALARIED_BLR_002', category: 'Apartment Rent', amount: 20000, dueDayOfMonth: 1, isMandatory: true },
      { id: 'OBL_BALLOON_FEE', customerId: 'CUST_SALARIED_BLR_002', category: 'Annual School Tuition Fee (Balloon)', amount: 42000, dueDayOfMonth: 20, isMandatory: true },
      { id: 'OBL_GROCERY', customerId: 'CUST_SALARIED_BLR_002', category: 'Essential Groceries', amount: 14000, dueDayOfMonth: 10, isMandatory: true },
    ]
  });

  // 3. MUST-HAVE SCENARIO 3: Gig Worker with Monsoon Earnings Volatility & Safe-to-Save Engine
  profiles.push({
    id: 'CUST_GIG_BLR_003',
    name: 'Ravi Kumar',
    archetype: 'GIG_WORKER',
    occupationOrIndustry: 'Ride-Hailing & Food Delivery Partner',
    clusterRegion: 'Bengaluru',
    panMasked: 'CWRPK4432K',
    udyamOrEshramNumber: 'ESHRAM-KN-9921-5541',
    accountOpeningDate: '2023-02-18',
    primaryBank: 'Paytm Payments Bank / IndusInd Bank',
    consent: {
      aaConsentHandle: 'CONSENT_AA_1109_221',
      status: 'ACTIVE',
      expiryDate: '2027-02-18',
      dataCompletenessPercentage: 92,
    },
    financialReality: {
      currentLiquidBalance: 4200,
      monthlyAverageIncome: 27500,
      monthlyEssentialExpenses: 18000,
      totalMonthlyDebtObligation: 2800,
      totalOutstandingDebt: 45000,
      cashRunwayDays: 22,
      criticalLiquidityDate: '2026-09-28',
      incomeVolatilityRatio: 0.42,
    },
    scores: {
      financialHealthScore: 54,
      contextualDistressScore: 66, // Seasonal weather-induced earnings drop
      distressStatus: 'WATCH',
      confidencePercentage: 89,
    },
    loans: [
      {
        id: 'LOAN_VEHICLE_01',
        customerId: 'CUST_GIG_BLR_003',
        lenderName: 'Bajaj Finance',
        lenderType: 'NBFC',
        loanType: 'VEHICLE_LOAN',
        principalAmount: 65000,
        outstandingPrincipal: 45000,
        interestRateAnnual: 16.5,
        monthlyEmi: 2800,
        tenureMonthsRemaining: 18,
        nachDebitDate: 10,
        dpd: 0,
        isAssetBacked: true,
      }
    ],
    obligations: [
      { id: 'OBL_ROOM_RENT', customerId: 'CUST_GIG_BLR_003', category: 'Room Rent', amount: 6000, dueDayOfMonth: 1, isMandatory: true },
      { id: 'OBL_FUEL', customerId: 'CUST_GIG_BLR_003', category: 'Daily Petrol & Maintenance', amount: 5500, dueDayOfMonth: 15, isMandatory: true },
      { id: 'OBL_RATION', customerId: 'CUST_GIG_BLR_003', category: 'Food & Family Living', amount: 6500, dueDayOfMonth: 5, isMandatory: true },
    ]
  });

  return profiles;
}

export function generateBulkProfiles(count: number = 100): CustomerProfile[] {
  const archetypes: CustomerArchetype[] = [
    'SALARIED', 'SELF_EMPLOYED', 'GIG_WORKER', 'FREELANCER', 
    'PROFESSIONAL', 'HOUSEHOLD', 'TRADER', 'MSME', 'MANUFACTURER', 'SEASONAL_BUSINESS'
  ];
  
  const bulk: CustomerProfile[] = [];

  for (let i = 1; i <= count; i++) {
    const arch = archetypes[i % archetypes.length];
    const cl = CLUSTERS[i % CLUSTERS.length];
    const incomeBase = arch === 'MSME' || arch === 'MANUFACTURER' ? 1500000 + (i * 20000) : 35000 + (i * 800);
    const health = 45 + Math.floor(Math.sin(i) * 35) + (i % 15);
    const distress = Math.max(10, Math.min(95, 100 - health + Math.floor(Math.cos(i) * 20)));

    let status: DistressStatus = 'HEALTHY';
    if (distress > 80) status = 'CRITICAL';
    else if (distress > 65) status = 'STRESSED';
    else if (distress > 50) status = 'VULNERABLE';
    else if (distress > 35) status = 'WATCH';

    bulk.push({
      id: `CUST_SYNTH_${String(i).padStart(4, '0')}`,
      name: `Synthetic Profile ${i} (${arch})`,
      archetype: arch,
      occupationOrIndustry: cl.industry,
      clusterRegion: cl.region,
      panMasked: `XXXXX${String(1000 + i).substring(0, 4)}X`,
      accountOpeningDate: '2023-01-01',
      primaryBank: i % 2 === 0 ? 'State Bank of India' : 'HDFC Bank',
      consent: {
        aaConsentHandle: `CONSENT_AA_SYNTH_${i}`,
        status: 'ACTIVE',
        expiryDate: '2027-01-01',
        dataCompletenessPercentage: 85 + (i % 15),
      },
      financialReality: {
        currentLiquidBalance: Math.round(incomeBase * 0.15),
        monthlyAverageIncome: incomeBase,
        monthlyEssentialExpenses: Math.round(incomeBase * 0.65),
        totalMonthlyDebtObligation: Math.round(incomeBase * 0.22),
        totalOutstandingDebt: Math.round(incomeBase * 2.8),
        cashRunwayDays: Math.max(8, Math.round(30 * (1 - distress / 100) + 5)),
        criticalLiquidityDate: `2026-09-${10 + (i % 18)}`,
        incomeVolatilityRatio: 0.15 + (i % 10) * 0.03,
      },
      scores: {
        financialHealthScore: Math.min(100, Math.max(10, health)),
        contextualDistressScore: distress,
        distressStatus: status,
        confidencePercentage: 88 + (i % 10),
      },
      loans: [],
      obligations: []
    });
  }

  return bulk;
}

export function saveAllDataToDisk(dataDir: string) {
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }

  const core = generateCoreScenarios();
  const bulk = generateBulkProfiles(100);
  const allProfiles = [...core, ...bulk];
  const benchmarks = generateSyntheticClusterBenchmarks();

  fs.writeFileSync(path.join(dataDir, 'profiles.json'), JSON.stringify(allProfiles, null, 2), 'utf8');
  fs.writeFileSync(path.join(dataDir, 'benchmarks.json'), JSON.stringify(benchmarks, null, 2), 'utf8');

  console.log(`[FINRES Generator] Successfully generated and saved:`);
  console.log(` - ${allProfiles.length} Total Customer Profiles (${core.length} detailed core scenarios + ${bulk.length} bulk)`);
  console.log(` - ${benchmarks.length} Cluster Benchmarks (6 Indian Clusters across 12 calendar months)`);
}

// Direct execution
if (require.main === module) {
  const targetDir = path.join(__dirname, '../../data');
  saveAllDataToDisk(targetDir);
}
