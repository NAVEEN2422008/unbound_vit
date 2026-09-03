import { CustomerProfile, IndustryClusterBenchmark, DistressStatus } from '../types/models';

export interface ContextIntelligenceResult {
  clusterRegion: string;
  industryOrOccupation: string;
  customerGrowthMomPercentage: number;
  clusterGrowthMomPercentage: number;
  deviationFromClusterPercentage: number;
  isSeasonalDip: boolean;
  contextualDistressScore: number; // 0 - 100
  distressStatus: DistressStatus;
  diagnosticExplanation: string;
}

/**
 * MODULE 3: Context-Aware Intelligence Engine (CIE)
 * Calibrates customer performance against Indian regional clusters and seasonal cycles.
 * Decouples normal seasonal dips from abnormal enterprise failure.
 */
export class ContextIntelligenceEngine {
  public static evaluateContextualDistress(
    profile: CustomerProfile,
    customerRecentRevenueDropPercentage: number, // e.g. -24 for 24% drop
    currentMonth: number,
    clusterBenchmarks: IndustryClusterBenchmark[]
  ): ContextIntelligenceResult {
    // 1. Find matching cluster benchmark
    const cluster = clusterBenchmarks.find(
      b => b.region.toLowerCase() === profile.clusterRegion.toLowerCase() && b.month === currentMonth
    );

    const clusterGrowthMom = cluster ? cluster.revenueGrowthPercentageMom : -5.0; // fallback standard dip
    const customerGrowthMom = customerRecentRevenueDropPercentage;
    
    // 2. Measure deviation from cluster normalcy
    // Example: Customer down 24%, Cluster down 5% => Customer is down 19% worse than peers!
    const deviation = customerGrowthMom - clusterGrowthMom;

    // 3. Determine if the dip is primarily seasonal
    // If cluster is significantly down (e.g. <= -15%) or customer is tracking within 5% of cluster, it is a seasonal dip!
    const isSeasonalDip = (clusterGrowthMom <= -15 && Math.abs(deviation) <= 8.0) || (Math.abs(deviation) <= 4.0 && customerGrowthMom < 0);

    // 4. Calculate Contextual Distress Score (0 - 100)
    let distressScore = 20;

    if (isSeasonalDip) {
      distressScore = 32; // Controlled watch/normal, not an enterprise crisis
    } else {
      if (deviation < -18) {
        distressScore = 85; // Structural critical deterioration
      } else if (deviation < -10) {
        distressScore = 70; // High vulnerability
      } else if (deviation < -5) {
        distressScore = 55; // Moderate stress
      } else {
        distressScore = 25; // Performing in line with or better than peers
      }
    }

    // 5. Categorize Distress Status
    let status: DistressStatus = 'HEALTHY';
    if (distressScore >= 80) status = 'CRITICAL';
    else if (distressScore >= 65) status = 'STRESSED';
    else if (distressScore >= 50) status = 'VULNERABLE';
    else if (distressScore >= 35) status = 'WATCH';

    let diagnosticExplanation = '';
    if (isSeasonalDip) {
      diagnosticExplanation = `Revenue declined by ${Math.abs(customerGrowthMom)}%, but comparable businesses in the ${profile.clusterRegion} ${profile.occupationOrIndustry} cluster declined by ${Math.abs(clusterGrowthMom)}% during this period. The decline is consistent with regional seasonal patterns.`;
    } else {
      diagnosticExplanation = `Customer revenue declined by ${Math.abs(customerGrowthMom)}%, whereas the ${profile.clusterRegion} cluster averaged ${clusterGrowthMom > 0 ? '+' : ''}${clusterGrowthMom}%. The borrower is deteriorating ${Math.abs(deviation).toFixed(1)}% faster than regional peers.`;
    }

    return {
      clusterRegion: profile.clusterRegion,
      industryOrOccupation: profile.occupationOrIndustry,
      customerGrowthMomPercentage: customerGrowthMom,
      clusterGrowthMomPercentage: clusterGrowthMom,
      deviationFromClusterPercentage: Number(deviation.toFixed(1)),
      isSeasonalDip,
      contextualDistressScore: distressScore,
      distressStatus: status,
      diagnosticExplanation
    };
  }
}
