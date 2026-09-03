"""
Obligation Collision Radar Service.
Detects exact calendar dates where known financial obligations (EMI, Rent, Payroll,
Supplier Payables, Taxes, Utilities, and Contractual Debits) exceed available liquidity.
Performs shortfall calculations, assigns severity levels (GREEN, YELLOW, ORANGE, RED),
and prioritizes collisions by severity, shortfall magnitude, and urgency.
Strictly descriptive: Identifies collisions without selecting loans or interventions.
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import math

from src_py.models.schemas import (
    NormalizedTransaction, LoanObligation, FixedObligationItem,
    ReceivableItem, PayableItem, DirectionEnum
)
from src_py.models.collision_radar_schemas import (
    CollisionSeverity, ObligationDueItem, ObligationCollisionEvent, ObligationCalendarReport
)


class ObligationCollisionRadarService:

    SEVERITY_WEIGHTS = {
        CollisionSeverity.RED: 10000.0,
        CollisionSeverity.ORANGE: 5000.0,
        CollisionSeverity.YELLOW: 1000.0,
        CollisionSeverity.GREEN: 0.0
    }

    @classmethod
    def detect_collisions(
        cls,
        customer_id: str,
        customer_name: str,
        archetype: str,
        starting_cash: float,
        transactions: List[NormalizedTransaction],
        loans: List[LoanObligation],
        obligations: List[FixedObligationItem],
        receivables: List[ReceivableItem],
        payables: List[PayableItem],
        horizon_days: int = 30,
        start_date: Optional[date] = None,
        minimum_buffer: Optional[float] = None
    ) -> ObligationCalendarReport:
        """
        Calculates available cash, obligation totals, projected balances, shortfalls,
        and severity for each future date in the horizon.
        
        Formula:
          available_cash = opening_cash + expected_inflows - non_obligation_outflows
          obligation_total = sum(obligations_due)
          projected_balance = available_cash - obligation_total
          shortfall = max(0, -projected_balance)
        """
        base_date = start_date or date.today()

        # Monthly & daily baselines
        monthly_emi = sum(l.monthly_emi for l in loans)
        monthly_fixed = sum(o.amount for o in obligations)
        daily_baseline_burn = max(200.0, (monthly_fixed + monthly_emi) / 30.0)
        min_buffer = minimum_buffer or round(daily_baseline_burn * 14.0, 2)  # 14-day lower buffer boundary

        # Conservative daily business inflow
        income_txns = [t for t in transactions if t.direction == DirectionEnum.INFLOW]
        total_income = sum(t.amount for t in income_txns)
        days_span = max(1, (max((t.timestamp.date() for t in transactions), default=base_date) - min((t.timestamp.date() for t in transactions), default=base_date)).days or 30)
        daily_expected_inflow = (total_income / days_span) * 0.85

        # Discretionary non-obligation daily outflow
        expense_txns = [t for t in transactions if t.direction == DirectionEnum.OUTFLOW]
        total_exp = sum(t.amount for t in expense_txns)
        daily_non_obligation_outflow = max(0.0, (total_exp - monthly_fixed - monthly_emi) / days_span)

        # Pre-group scheduled items by date
        receivables_by_date: Dict[date, List[ReceivableItem]] = {}
        for r in receivables:
            target_date = r.expected_collection_date or r.due_date
            if target_date not in receivables_by_date:
                receivables_by_date[target_date] = []
            receivables_by_date[target_date].append(r)

        payables_by_date: Dict[date, List[PayableItem]] = {}
        for p in payables:
            if p.due_date not in payables_by_date:
                payables_by_date[p.due_date] = []
            payables_by_date[p.due_date].append(p)

        obligations_by_day: Dict[int, List[FixedObligationItem]] = {}
        for o in obligations:
            day = min(max(1, o.due_day_of_month), 28)
            if day not in obligations_by_day:
                obligations_by_day[day] = []
            obligations_by_day[day].append(o)

        loans_by_day: Dict[int, List[LoanObligation]] = {}
        for l in loans:
            day = min(max(1, l.nach_debit_day), 28)
            if day not in loans_by_day:
                loans_by_day[day] = []
            loans_by_day[day].append(l)

        calendar_events: List[ObligationCollisionEvent] = []
        running_cash = starting_cash
        total_shortfall_vol = 0.0
        first_severe_date: Optional[date] = None

        for i in range(horizon_days):
            current_date = base_date + timedelta(days=i)
            opening_cash = running_cash

            # 1. Expected Inflows for this date
            expected_inflows = daily_expected_inflow
            if current_date in receivables_by_date:
                expected_inflows += sum(r.amount for r in receivables_by_date[current_date])

            # 2. Non-obligation outflows
            non_ob_outflow = daily_non_obligation_outflow

            # 3. Available Cash before contractual obligations
            available_cash = opening_cash + expected_inflows - non_ob_outflow

            # 4. Collect all obligations due on this date
            obligations_due: List[ObligationDueItem] = []

            # NACH loan EMIs
            if current_date.day in loans_by_day:
                for l in loans_by_day[current_date.day]:
                    obligations_due.append(ObligationDueItem(
                        id=f"OB_LOAN_{l.id}_{current_date}",
                        obligation_type="EMI",
                        title=f"{l.lender_name} Loan EMI ({l.loan_type})",
                        counterparty=l.lender_name,
                        amount=l.monthly_emi,
                        is_mandatory=True,
                        penalty_on_default="NACH Bounce Charges + CIBIL DPD Impact"
                    ))

            # Fixed obligations (Rent, Payroll, Utilities, Taxes)
            if current_date.day in obligations_by_day:
                for o in obligations_by_day[current_date.day]:
                    ob_type = "RENT" if "RENT" in o.category.upper() else (
                        "PAYROLL" if "PAYROLL" in o.category.upper() else (
                            "TAX" if "TAX" in o.category.upper() else "UTILITY"
                        )
                    )
                    obligations_due.append(ObligationDueItem(
                        id=f"OB_FIXED_{o.id}_{current_date}",
                        obligation_type=ob_type,
                        title=f"{o.category} Fixed Obligation",
                        counterparty=o.category,
                        amount=o.amount,
                        is_mandatory=o.is_mandatory,
                        penalty_on_default="Late fee / service disruption"
                    ))

            # Supplier Payables
            if current_date in payables_by_date:
                for p in payables_by_date[current_date]:
                    obligations_due.append(ObligationDueItem(
                        id=f"OB_PAYABLE_{p.id}_{current_date}",
                        obligation_type="SUPPLIER",
                        title=f"Vendor Invoice: {p.vendor_name}",
                        counterparty=p.vendor_name,
                        amount=p.amount,
                        is_mandatory=p.is_critical_supply,
                        penalty_on_default="Commercial Supply Stoppage"
                    ))

            obligation_total = sum(ob.amount for ob in obligations_due)

            # 5. Projected balance & shortfall
            projected_balance = available_cash - obligation_total
            shortfall = max(0.0, -projected_balance)
            total_shortfall_vol += shortfall

            # 6. Severity determination
            # GREEN: healthy liquidity buffer (projected balance >= min_buffer)
            # YELLOW: low buffer (0 <= projected balance < min_buffer)
            # ORANGE: projected shortage (0 < shortfall <= 50,000 or <= 1.5x daily burn)
            # RED: severe shortage (shortfall > 50,000 or significant multi-obligation collision)
            if projected_balance >= min_buffer:
                severity = CollisionSeverity.GREEN
            elif projected_balance >= 0:
                severity = CollisionSeverity.YELLOW
            elif shortfall <= max(50000.0, daily_baseline_burn * 2.0):
                severity = CollisionSeverity.ORANGE
            else:
                severity = CollisionSeverity.RED

            if severity == CollisionSeverity.RED and not first_severe_date:
                first_severe_date = current_date

            # Priority score: Higher severity weight, higher shortfall, and higher urgency (earlier days)
            days_until = i
            urgency_score = max(0, 100 - days_until)
            priority_score = (
                cls.SEVERITY_WEIGHTS[severity] +
                (shortfall * 1.0) +
                (urgency_score * 5.0)
            )

            event = ObligationCollisionEvent(
                date=current_date,
                days_until_event=days_until,
                obligation_total=round(obligation_total, 2),
                expected_cash=round(available_cash, 2),
                projected_balance=round(projected_balance, 2),
                shortfall=round(shortfall, 2),
                severity=severity,
                priority_score=round(priority_score, 2),
                contributing_obligations=obligations_due
            )
            calendar_events.append(event)

            # Update running cash for next date
            running_cash = projected_balance

        # Filter and sort collisions (RED, ORANGE, YELLOW with obligations due)
        collisions = [
            e for e in calendar_events 
            if e.severity in (CollisionSeverity.RED, CollisionSeverity.ORANGE, CollisionSeverity.YELLOW) 
            and e.obligation_total > 0
        ]
        
        # Sort collisions by:
        # 1. Severity rank (RED > ORANGE > YELLOW > GREEN)
        # 2. Shortfall amount (descending)
        # 3. Days until event (ascending - sooner is more urgent)
        severity_rank = {
            CollisionSeverity.RED: 4,
            CollisionSeverity.ORANGE: 3,
            CollisionSeverity.YELLOW: 2,
            CollisionSeverity.GREEN: 1
        }
        prioritized = sorted(
            collisions,
            key=lambda x: (severity_rank[x.severity], x.shortfall, -x.days_until_event),
            reverse=True
        )

        critical_count = sum(1 for e in calendar_events if e.severity in (CollisionSeverity.RED, CollisionSeverity.ORANGE))

        summary_text = (
            f"Obligation Collision Radar scanned {horizon_days} days. Detected {critical_count} critical collision dates "
            f"with total shortfall volume of ₹{total_shortfall_vol:,.0f}."
        )
        if first_severe_date:
            days_to_first = (first_severe_date - base_date).days
            summary_text += f" Earliest severe shortfall occurs on {first_severe_date.isoformat()} ({days_to_first} days ahead)."

        return ObligationCalendarReport(
            customer_id=customer_id,
            customer_name=customer_name,
            archetype=archetype,
            as_of_date=base_date,
            horizon_days=horizon_days,
            total_obligations_tracked=round(sum(e.obligation_total for e in calendar_events), 2),
            total_shortfall_volume=round(total_shortfall_vol, 2),
            critical_collision_count=critical_count,
            first_severe_shortfall_date=first_severe_date,
            prioritized_collisions=prioritized,
            calendar_events=calendar_events,
            radar_summary=summary_text
        )
