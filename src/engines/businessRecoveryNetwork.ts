export interface B2BEnterpriseMatch {
  matchId: string;
  sourceSupplierId: string;
  sourceSupplierName: string;
  targetBuyerId: string;
  targetBuyerName: string;
  productCategory: string;
  clusterRegion: string;
  compatibilityScorePercentage: number;
  matchingRationale: string;
  privacyStatus: 'DOUBLE_BLIND_LOCKED' | 'SUPPLIER_CONSENTED' | 'BUYER_CONSENTED' | 'MUTUAL_OPT_IN_EXCHANGED';
  estimatedMonthlyRevenuePotential: number;
}

/**
 * MODULE 8: Consent-Based B2B Business Recovery Network (ONDC Interoperable)
 * Matches order-deficient MSMEs with bank corporate buyers without exposing financial distress data.
 */
export class BusinessRecoveryNetwork {
  private static registeredMatches: B2BEnterpriseMatch[] = [
    {
      matchId: 'MATCH_B2B_9921',
      sourceSupplierId: 'CUST_MSME_TIRUPPUR_001',
      sourceSupplierName: 'Sri Balaji Fabrics & Knits',
      targetBuyerId: 'CORP_BUYER_MUMBAI_088',
      targetBuyerName: 'Aditya Birla Fashion & Retail Supply Division',
      productCategory: 'Organic Combed Cotton Fabric (180 GSM)',
      clusterRegion: 'Tiruppur ↔ Mumbai',
      compatibilityScorePercentage: 92,
      matchingRationale: 'Buyer requires 15,000 meters/month combed cotton fabric; Supplier has active high-speed circular knitting lines operating at idle capacity.',
      privacyStatus: 'DOUBLE_BLIND_LOCKED',
      estimatedMonthlyRevenuePotential: 450000
    },
    {
      matchId: 'MATCH_B2B_9922',
      sourceSupplierId: 'CUST_MSME_TIRUPPUR_001',
      sourceSupplierName: 'Sri Balaji Fabrics & Knits',
      targetBuyerId: 'CORP_BUYER_BLR_012',
      targetBuyerName: 'Zudio / Trent Sourcing Hub (ONDC Network)',
      productCategory: 'Knitwear Basics & Round-Neck T-Shirt Fabric',
      clusterRegion: 'Tiruppur ↔ Bengaluru',
      compatibilityScorePercentage: 88,
      matchingRationale: 'High geographic proximity on Bengaluru logistics corridor; supplier meets vendor quality rating (8.8/10).',
      privacyStatus: 'DOUBLE_BLIND_LOCKED',
      estimatedMonthlyRevenuePotential: 380000
    }
  ];

  public static findOpportunitiesForSupplier(supplierId: string): B2BEnterpriseMatch[] {
    return this.registeredMatches.filter(m => m.sourceSupplierId === supplierId);
  }

  public static grantConsent(matchId: string, party: 'SUPPLIER' | 'BUYER'): B2BEnterpriseMatch | null {
    const match = this.registeredMatches.find(m => m.matchId === matchId);
    if (!match) return null;

    if (party === 'SUPPLIER') {
      match.privacyStatus = match.privacyStatus === 'BUYER_CONSENTED' ? 'MUTUAL_OPT_IN_EXCHANGED' : 'SUPPLIER_CONSENTED';
    } else {
      match.privacyStatus = match.privacyStatus === 'SUPPLIER_CONSENTED' ? 'MUTUAL_OPT_IN_EXCHANGED' : 'BUYER_CONSENTED';
    }

    return match;
  }
}
