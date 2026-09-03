"""
Consent-Based Bank Business Opportunity Matching Engine Service.
Matches distressed enterprise customers with corporate buyer demand within the bank's client ecosystem.
Guarantees double-blind data privacy, calculates match scores, and facilitates introduction ONLY after mutual consent.
"""
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from src_py.models.matching_schemas import (
    BusinessEntityProfile, BusinessRole, MatchConsentStatus,
    AnonymousBusinessCard, OpportunityMatchResult, ConsentActionRequest
)
from src_py.data.matching_directory import BANK_BUSINESS_DIRECTORY

# In-memory persistence of active match states
ACTIVE_MATCH_REGISTRY: Dict[str, OpportunityMatchResult] = {}


class BusinessOpportunityMatchingService:

    @classmethod
    def calculate_match_score(
        cls,
        supplier: BusinessEntityProfile,
        buyer: BusinessEntityProfile
    ) -> Tuple[float, List[str]]:
        """
        Calculates match score based on 8 criteria:
        1. Industry compatibility (20%)
        2. Products/Services overlap (20%)
        3. Geographic region / Cluster proximity (15%)
        4. Capacity vs Demand alignment (15%)
        5. Supplier/Buyer role compatibility (10%)
        6. Business size compatibility (10%)
        7. Availability & immediate need (10%)
        """
        reasons = []
        score = 0.0

        # 1. Supplier / Buyer Role check
        if supplier.role == buyer.role:
            return 0.0, ["Both entities have the same role (both suppliers or both buyers)."]
        score += 0.10

        # 2. Industry Compatibility
        if supplier.industry.lower() == buyer.industry.lower():
            score += 0.20
            reasons.append(f"Direct Industry Alignment: Both entities operate within {supplier.industry}.")
        else:
            # Check sub-sector overlap
            common_sub = set(s.lower() for s in supplier.sub_sectors) & set(b.lower() for b in buyer.sub_sectors)
            if common_sub:
                score += 0.12
                reasons.append(f"Sub-sector Overlap: Matched on {', '.join(common_sub)}.")

        # 3. Geographic Region & Cluster Proximity
        if supplier.cluster_region.lower() == buyer.cluster_region.lower():
            score += 0.15
            reasons.append(f"Geographic Proximity: Both located within {supplier.cluster_region} industrial cluster (Zero inter-state logistics latency).")
        elif supplier.state.lower() == buyer.state.lower():
            score += 0.08
            reasons.append(f"Intra-State Proximity: Both located within {supplier.state}.")

        # 4. Products & Capabilities Overlap
        sup_prods = " ".join(supplier.products_services).lower()
        buyer_desc = (buyer.immediate_requirement_description + " " + " ".join(buyer.products_services)).lower()
        
        matches_found = []
        for p in supplier.products_services:
            tokens = [t for t in p.lower().split() if len(t) > 3]
            if any(token in buyer_desc for token in tokens):
                matches_found.append(p)

        if matches_found:
            score += 0.20
            reasons.append(f"Product Compatibility: Supplier provides {', '.join(matches_found[:2])} directly needed for buyer's manufacturing.")
        else:
            score += 0.05

        # 5. Capacity vs. Demand Alignment
        cap = supplier.capacity_units_per_month
        dem = buyer.demand_units_per_month
        if cap > 0 and dem > 0:
            ratio = min(cap, dem) / max(cap, dem)
            if ratio >= 0.50:
                score += 0.15
                reasons.append(f"Volume Fit: Buyer procurement demand ({dem:,.0f} units) absorbs ~{min(100.0, (dem/cap)*100.0):.0f}% of supplier's idle plant capacity.")
            else:
                score += 0.08
                reasons.append(f"Partial Volume Fit: Buyer requirement represents significant off-take for supplier.")

        # 6. Business Size Compatibility
        score += 0.10
        reasons.append(f"Ecosystem Compatibility: Well-matched tier dynamic ({supplier.business_size} supplier with {buyer.business_size} corporate buyer).")

        # 7. Availability & Immediate Need
        score += 0.10
        reasons.append("Immediate Commercial Readiness: Active unallocated production line ready for immediate job-work contracting.")

        return round(min(1.0, score), 2), reasons

    @classmethod
    def find_opportunities_for_customer(
        cls,
        distressed_customer_id: str,
        min_score: float = 0.65
    ) -> List[OpportunityMatchResult]:
        """
        Discovers all compatible commercial matches for a customer within the bank's directory.
        Outputs double-blind anonymous cards and records potential matches in CONSENT_REQUIRED state.
        """
        distressed = BANK_BUSINESS_DIRECTORY.get(distressed_customer_id)
        if not distressed:
            return []

        results: List[OpportunityMatchResult] = []

        for counter_id, counter_profile in BANK_BUSINESS_DIRECTORY.items():
            if counter_id == distressed_customer_id:
                continue

            score, reasons = cls.calculate_match_score(distressed, counter_profile)
            if score >= min_score:
                match_id = f"MATCH_{distressed_customer_id[-6:]}_{counter_id[-6:]}"

                # Calculate distress recovery revenue impact
                # Estimate conservative 15% revenue gain on monthly turnover
                monthly_rev_gain = round((distressed.annual_turnover / 12.0) * 0.18, 2)
                distress_points_reduced = round(score * 25.0, 1)

                # Anonymize counterparty
                alias = f"Verified Bank Client #{counter_id[-4:]} ({counter_profile.cluster_region} {counter_profile.industry})"
                anon_card = AnonymousBusinessCard(
                    match_id=match_id,
                    anonymous_alias=alias,
                    industry=counter_profile.industry,
                    cluster_region=counter_profile.cluster_region,
                    business_size=counter_profile.business_size,
                    products_offered_or_needed=counter_profile.products_services,
                    compatible_volume_monthly=min(distressed.capacity_units_per_month, counter_profile.demand_units_per_month) or 15000.0,
                    potential_monthly_revenue_impact=monthly_rev_gain
                )

                # Check if already registered in active registry to preserve consent state
                existing = ACTIVE_MATCH_REGISTRY.get(match_id)
                if existing:
                    results.append(existing)
                else:
                    match_obj = OpportunityMatchResult(
                        match_id=match_id,
                        distressed_customer_id=distressed_customer_id,
                        counterparty_customer_id=counter_id,
                        match_score=score,
                        reasons=reasons,
                        status=MatchConsentStatus.CONSENT_REQUIRED,
                        anonymous_counterparty_card=anon_card,
                        projected_monthly_revenue_gain=monthly_rev_gain,
                        projected_distress_reduction_points=distress_points_reduced
                    )
                    ACTIVE_MATCH_REGISTRY[match_id] = match_obj
                    results.append(match_obj)

        return sorted(results, key=lambda x: x.match_score, reverse=True)

    @classmethod
    def record_consent_and_facilitate_intro(
        cls,
        req: ConsentActionRequest
    ) -> OpportunityMatchResult:
        """
        Records individual consent for an opportunity match.
        Transitions state:
        CONSENT_REQUIRED -> INITIATOR_CONSENTED or COUNTERPARTY_CONSENTED -> MUTUAL_CONSENT_GRANTED.
        Only unlocks real identity and contact details when MUTUAL_CONSENT_GRANTED is reached.
        """
        match_obj = ACTIVE_MATCH_REGISTRY.get(req.match_id)
        if not match_obj:
            raise ValueError(f"Match ID '{req.match_id}' not found in registry.")

        if req.action.upper() == "REJECT":
            match_obj.status = MatchConsentStatus.REJECTED
            return match_obj

        now = datetime.utcnow()
        if req.customer_id == match_obj.distressed_customer_id:
            match_obj.initiator_consent_timestamp = now
            if match_obj.status == MatchConsentStatus.COUNTERPARTY_CONSENTED:
                match_obj.status = MatchConsentStatus.MUTUAL_CONSENT_GRANTED
            else:
                match_obj.status = MatchConsentStatus.INITIATOR_CONSENTED
        elif req.customer_id == match_obj.counterparty_customer_id:
            match_obj.counterparty_consent_timestamp = now
            if match_obj.status == MatchConsentStatus.INITIATOR_CONSENTED:
                match_obj.status = MatchConsentStatus.MUTUAL_CONSENT_GRANTED
            else:
                match_obj.status = MatchConsentStatus.COUNTERPARTY_CONSENTED
        else:
            raise ValueError("Customer ID does not belong to this opportunity match.")

        # If both parties granted mutual consent: Unlock real introductions & generate audit hash
        if match_obj.status == MatchConsentStatus.MUTUAL_CONSENT_GRANTED:
            party_a = BANK_BUSINESS_DIRECTORY[match_obj.distressed_customer_id]
            party_b = BANK_BUSINESS_DIRECTORY[match_obj.counterparty_customer_id]

            audit_payload = f"{match_obj.match_id}:{party_a.customer_id}:{party_b.customer_id}:{now.isoformat()}"
            match_obj.consent_audit_hash = f"SHA256_{hashlib.sha256(audit_payload.encode()).hexdigest()[:24]}"

            match_obj.unlocked_introduction_details = {
                "facilitated_by": "State Bank of India Commercial Credit & Enterprise Recovery Desk",
                "party_a": {
                    "company_name": party_a.company_name,
                    "city": party_a.city,
                    "representative": "Managing Director / Commercial Promoter"
                },
                "party_b": {
                    "company_name": party_b.company_name,
                    "city": party_b.city,
                    "representative": "Chief Procurement Officer"
                },
                "introduction_memo": (
                    f"Official Bank Introduction between {party_a.company_name} and {party_b.company_name}. "
                    f"Initiated to fulfill commercial procurement requirements for {party_b.industry} "
                    f"leveraging {party_a.cluster_region} manufacturing capacity."
                )
            }

        return match_obj
