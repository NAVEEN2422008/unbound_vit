import { CustomerProfile } from '../types/models';
import { FinancialRealityEngine, FinancialRealityMetrics } from './financialRealityEngine';
import { ContextIntelligenceEngine, ContextIntelligenceResult } from './contextIntelligenceEngine';
import { ObligationCollisionRadar, CollisionRadarReport } from './obligationCollisionRadar';
import { AssetEconomicEngine, EnterpriseAssetDiagnostic } from './assetEconomicEngine';
import { generateSyntheticClusterBenchmarks } from '../data/benchmarks';

export interface ComprehensiveDiagnosisReport {
  customerId: string;
  customerName: string;
  archetype: string;
  financialReality: FinancialRealityMetrics;
  contextIntelligence: ContextIntelligenceResult;
  collisionRadar: CollisionRadarReport;
  assetDiagnostic: EnterpriseAssetDiagnostic;
  executiveSummary: string;
}

/**
 * FINRES Core Intelligence Coordinator
 * Coordinates Modules 2, 3, 4, and 5 into a unified diagnostic synthesis.
 */
export class FinresDiagnosticCoordinator {
  public static diagnoseCustomer(
    profile: CustomerProfile,
    recentRevenueChangePercentage: number = -24.0,
    currentMonth: number = 9
  ): ComprehensiveDiagnosisReport {
    const benchmarks = generateSyntheticClusterBenchmarks();

    const fre = FinancialRealityEngine.computeFinancialReality(profile);
    const cie = ContextIntelligenceEngine.evaluateContextualDistress(
      profile,
      recentRevenueChangePercentage,
      currentMonth,
      benchmarks
    );
    const ocr = ObligationCollisionRadar.projectTrajectory(profile, 30);
    const ale = AssetEconomicEngine.diagnoseEnterpriseAssets(profile);

    let summary = `Customer ${profile.name} (${profile.archetype}) in ${profile.clusterRegion}. `;
    summary += `Financial Health Score: ${fre.financialHealthScore}/100, Contextual Distress Score: ${cie.contextualDistressScore}/100 (${cie.distressStatus}). `;
    if (ocr.criticalLiquidityDate) {
      summary += `Projected Critical Liquidity Collision in ${ocr.daysUntilCollision} days (${ocr.criticalLiquidityDate}). `;
    }
    if (ale.lossMakingAssetsCount > 0) {
      summary += `Deterioration driven by ${ale.lossMakingAssetsCount} loss-making asset(s).`;
    }

    return {
      customerId: profile.id,
      customerName: profile.name,
      archetype: profile.archetype,
      financialReality: fre,
      contextIntelligence: cie,
      collisionRadar: ocr,
      assetDiagnostic: ale,
      executiveSummary: summary
    };
  }
}
