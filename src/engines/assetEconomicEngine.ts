import { CustomerProfile, BusinessAsset } from '../types/models';

export interface AssetAnalysisSummary {
  assetId: string;
  name: string;
  monthlyAttributableRevenue: number;
  monthlyOperatingCost: number;
  monthlyDedicatedEmi: number;
  netMonthlyContribution: number;
  status: 'PRODUCTIVE' | 'MARGINAL' | 'LOSS_MAKING' | 'IDLE';
  efficiencyRatio: number; // Revenue / (Cost + EMI)
  actionableRecommendation: string;
}

export interface EnterpriseAssetDiagnostic {
  totalAssetsCount: number;
  totalAssetRevenue: number;
  totalAssetOperatingCost: number;
  totalAssetDebtEmi: number;
  netAssetEbitdaContribution: number;
  lossMakingAssetsCount: number;
  assetBreakdown: AssetAnalysisSummary[];
  strategicDiagnosis: string;
}

/**
 * MODULE 5: Asset-Level Economic Engine (ALE)
 * Disaggregates MSME revenue, operational burn, and loan burden machine by machine.
 * Isolates cash-burning capital assets from healthy production lines.
 */
export class AssetEconomicEngine {
  public static diagnoseEnterpriseAssets(profile: CustomerProfile): EnterpriseAssetDiagnostic {
    if (!profile.assets || profile.assets.length === 0) {
      return {
        totalAssetsCount: 0,
        totalAssetRevenue: 0,
        totalAssetOperatingCost: 0,
        totalAssetDebtEmi: 0,
        netAssetEbitdaContribution: 0,
        lossMakingAssetsCount: 0,
        assetBreakdown: [],
        strategicDiagnosis: 'No discrete physical machinery or asset loans registered for this profile.'
      };
    }

    const breakdown: AssetAnalysisSummary[] = profile.assets.map(asset => {
      // Find dedicated term loan EMI if linked
      const linkedLoan = profile.loans.find(l => l.id === asset.dedicatedLoanId || l.assetRefId === asset.id);
      const dedicatedEmi = linkedLoan ? linkedLoan.monthlyEmi : 0;

      const totalBurden = asset.monthlyOperatingCost + dedicatedEmi;
      const netContribution = asset.monthlyAttributableRevenue - totalBurden;
      const efficiencyRatio = totalBurden > 0 ? Number((asset.monthlyAttributableRevenue / totalBurden).toFixed(2)) : 1.0;

      let status: 'PRODUCTIVE' | 'MARGINAL' | 'LOSS_MAKING' | 'IDLE' = 'PRODUCTIVE';
      let recommendation = 'Asset is economically productive. Maintain utilization.';

      if (netContribution < 0) {
        status = 'LOSS_MAKING';
        recommendation = `Asset generates negative net cash flow (-₹${Math.abs(netContribution).toLocaleString('en-IN')}/mo). Recommend restructuring machinery loan tenure, subleasing capacity, or disposal.`;
      } else if (netContribution < 25000 || efficiencyRatio < 1.1) {
        status = 'MARGINAL';
        recommendation = 'Marginal cash yield. Optimize power/operator overheads or seek higher-margin orders.';
      }

      return {
        assetId: asset.id,
        name: asset.name,
        monthlyAttributableRevenue: asset.monthlyAttributableRevenue,
        monthlyOperatingCost: asset.monthlyOperatingCost,
        monthlyDedicatedEmi: dedicatedEmi,
        netMonthlyContribution: netContribution,
        status,
        efficiencyRatio,
        actionableRecommendation: recommendation
      };
    });

    const totalRevenue = breakdown.reduce((sum, a) => sum + a.monthlyAttributableRevenue, 0);
    const totalCost = breakdown.reduce((sum, a) => sum + a.monthlyOperatingCost, 0);
    const totalEmi = breakdown.reduce((sum, a) => sum + a.monthlyDedicatedEmi, 0);
    const netEbitda = totalRevenue - totalCost - totalEmi;
    const lossMakingCount = breakdown.filter(a => a.status === 'LOSS_MAKING').length;

    const strategicDiagnosis = lossMakingCount > 0
      ? `Enterprise operations are healthy across primary lines, but cash flow is drained by ${lossMakingCount} underperforming asset(s) with dedicated term loans. Restructuring targeted asset liabilities will restore enterprise solvency.`
      : 'All physical assets are cash-flow positive and cover their dedicated loan burdens.';

    return {
      totalAssetsCount: breakdown.length,
      totalAssetRevenue: totalRevenue,
      totalAssetOperatingCost: totalCost,
      totalAssetDebtEmi: totalEmi,
      netAssetEbitdaContribution: netEbitda,
      lossMakingAssetsCount: lossMakingCount,
      assetBreakdown: breakdown,
      strategicDiagnosis
    };
  }
}
