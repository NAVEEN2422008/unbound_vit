import { CustomerProfile, IndustryClusterBenchmark } from '../types/models';

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
      let seasonalFactor = 1.0;
      let growthMom = 2.0;

      if (cl.region === 'Tiruppur' && (month === 1 || month === 2)) {
        seasonalFactor = 0.78; // Post-holiday seasonal export lull
        growthMom = -22.0;
      } else if (cl.region === 'Morbi' && (month === 7 || month === 8)) {
        seasonalFactor = 0.82; // Monsoon slowdown
        growthMom = -18.0;
      } else if (cl.region === 'Surat' && (month === 10 || month === 11)) {
        seasonalFactor = 1.35; // Diwali surge
        growthMom = 28.0;
      } else if (cl.region === 'Tiruppur' && month === 9) {
        seasonalFactor = 0.95;
        growthMom = -5.0;
      }

      benchmarks.push({
        clusterId: `CLUST_${idx + 1}`,
        industry: cl.industry,
        region: cl.region,
        month,
        averageRevenueIndex: Math.round(100 * seasonalFactor),
        revenueGrowthPercentageMom: growthMom,
        seasonalVolatilityIndex: 0.18,
        typicalOperatingMargin: 0.22,
      });
    }
  });

  return benchmarks;
}
