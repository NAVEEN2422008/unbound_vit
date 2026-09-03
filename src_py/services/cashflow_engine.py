"""
Cash-Flow Timeline Engine Service.
Determines how cash moves through customer accounts daily and uncovers temporary
liquidity collisions hidden behind positive monthly aggregate income.
Generates conservative 30-day, 60-day, and 90-day forward forecasts with
obligation markers, receivable markers, and deficit signals.
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import math

from src_py.models.schemas import (
    NormalizedTransaction, LoanObligation, FixedObligationItem,
    ReceivableItem, PayableItem, DirectionEnum, ValueProvenance
)
from src_py.models.cashflow_schemas import (
    DailyTimelineRecord, WeeklySummaryRecord, CashflowForecastHorizon, CashflowForecastReport
)


class CashflowTimelineEngineService:

    @classmethod
    def generate_timeline(
        cls,
        customer_id: str,
        starting_cash: float,
        transactions: List[NormalizedTransaction],
        loans: List[LoanObligation],
        obligations: List[FixedObligationItem],
        receivables: List[ReceivableItem],
        payables: List[PayableItem],
        horizon_days: int = 30,
        start_date: Optional[date] = None,
        minimum_required_cash: Optional[float] = None
    ) -> CashflowForecastHorizon:
        """
        Generates daily cash timeline for horizon_days (30, 60, or 90 days).
        Daily formula:
          closing_balance = opening_balance + actual_inflows + expected_inflows - actual_outflows - expected_outflows
        Tracks obligation markers, receivable markers, minimum required cash, surplus, and shortfall.
        """
        current_date = start_date or date.today()
        end_date = current_date + timedelta(days=horizon_days - 1)

        # Baseline recurring daily burn estimation (conservative)
        monthly_emi = sum(l.monthly_emi for l in loans)
        monthly_fixed_costs = sum(o.amount for o in obligations)
        daily_baseline_burn = max(200.0, (monthly_fixed_costs + monthly_emi) / 30.0)

        # 21-day prudential liquidity cushion
        min_cash_cushion = minimum_required_cash or round(daily_baseline_burn * 21.0, 2)

        # Historical average daily income for conservative baseline expected income
        income_txns = [t for t in transactions if t.direction == DirectionEnum.INFLOW]
        total_hist_income = sum(t.amount for t in income_txns)
        days_covered = max(1, (max((t.timestamp.date() for t in transactions), default=current_date) - min((t.timestamp.date() for t in transactions), default=current_date)).days or 30)
        conservative_daily_income = (total_hist_income / days_covered) * 0.85  # 15% conservative haircut

        # Past actual transactions map by date
        actual_in_map: Dict[date, float] = {}
        actual_out_map: Dict[date, float] = {}
        for t in transactions:
            t_d = t.timestamp.date()
            if t.direction == DirectionEnum.INFLOW:
                actual_in_map[t_d] = actual_in_map.get(t_d, 0.0) + t.amount
            else:
                actual_out_map[t_d] = actual_out_map.get(t_d, 0.0) + t.amount

        # Build schedule maps for expected inflows & outflows
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

        daily_records: List[DailyTimelineRecord] = []
        running_balance = starting_cash
        earliest_shortfall: Optional[date] = None
        peak_deficit: float = 0.0
        total_inflows_acc = 0.0
        total_outflows_acc = 0.0

        for i in range(horizon_days):
            d = current_date + timedelta(days=i)
            opening = running_balance

            # Actuals (if date is today or past)
            actual_in = actual_in_map.get(d, 0.0)
            actual_out = actual_out_map.get(d, 0.0)

            # Expected Inflows: Receivables + conservative business income
            expected_in = 0.0
            rec_markers: List[Dict[str, Any]] = []
            if d in receivables_by_date:
                for r in receivables_by_date[d]:
                    expected_in += r.amount
                    rec_markers.append({
                        "id": r.id,
                        "invoice": r.invoice_number,
                        "buyer": r.buyer_name,
                        "amount": r.amount,
                        "is_treds_eligible": r.is_treds_eligible
                    })
            if actual_in == 0.0:
                expected_in += conservative_daily_income

            # Expected Outflows: EMI + Obligations + Payables
            expected_out = 0.0
            ob_markers: List[Dict[str, Any]] = []

            # NACH loan debit
            if d.day in loans_by_day:
                for l in loans_by_day[d.day]:
                    expected_out += l.monthly_emi
                    ob_markers.append({
                        "type": "LOAN_EMI_NACH",
                        "lender": l.lender_name,
                        "amount": l.monthly_emi,
                        "tenure_left": l.tenure_months_remaining
                    })

            # Fixed obligations (Rent, Payroll, Electricity)
            if d.day in obligations_by_day:
                for o in obligations_by_day[d.day]:
                    expected_out += o.amount
                    ob_markers.append({
                        "type": "FIXED_OBLIGATION",
                        "category": o.category,
                        "amount": o.amount
                    })

            # Supplier payables
            if d in payables_by_date:
                for p in payables_by_date[d]:
                    expected_out += p.amount
                    ob_markers.append({
                        "type": "SUPPLIER_PAYABLE",
                        "vendor": p.vendor_name,
                        "amount": p.amount,
                        "is_critical": p.is_critical_supply
                    })

            # Daily balance computation
            closing = opening + actual_in + expected_in - actual_out - expected_out
            running_balance = closing

            total_inflows_acc += (actual_in + expected_in)
            total_outflows_acc += (actual_out + expected_out)

            # Shortfall / Surplus against minimum required cash
            surplus = max(0.0, closing - min_cash_cushion)
            shortfall = max(0.0, min_cash_cushion - closing) if closing < min_cash_cushion else (abs(closing) if closing < 0 else 0.0)
            is_deficit = (closing < 0.0)

            if is_deficit:
                if not earliest_shortfall:
                    earliest_shortfall = d
                if abs(closing) > peak_deficit:
                    peak_deficit = abs(closing)

            data_status = ValueProvenance.ACTUAL if d <= date.today() and (actual_in > 0 or actual_out > 0) else ValueProvenance.PREDICTED

            daily_records.append(DailyTimelineRecord(
                date=d,
                opening_balance=round(opening, 2),
                actual_inflow=round(actual_in, 2),
                expected_inflow=round(expected_in, 2),
                actual_outflow=round(actual_out, 2),
                expected_outflow=round(expected_out, 2),
                closing_balance=round(closing, 2),
                minimum_required_cash=round(min_cash_cushion, 2),
                surplus=round(surplus, 2),
                shortfall=round(shortfall, 2),
                data_status=data_status,
                obligation_markers=ob_markers,
                receivable_markers=rec_markers,
                is_liquidity_deficit=is_deficit
            ))

        # Build Weekly Rollups
        weekly_records: List[WeeklySummaryRecord] = []
        for w_idx in range(math.ceil(horizon_days / 7.0)):
            chunk = daily_records[w_idx * 7 : (w_idx + 1) * 7]
            if not chunk:
                continue
            w_start = chunk[0].date
            w_end = chunk[-1].date
            w_in = sum(c.actual_inflow + c.expected_inflow for c in chunk)
            w_out = sum(c.actual_outflow + c.expected_outflow for c in chunk)
            w_end_balance = chunk[-1].closing_balance
            has_def = any(c.is_liquidity_deficit for c in chunk)

            weekly_records.append(WeeklySummaryRecord(
                week_number=w_idx + 1,
                week_start_date=w_start,
                week_end_date=w_end,
                total_inflows=round(w_in, 2),
                total_outflows=round(w_out, 2),
                net_cash_flow=round(w_in - w_out, 2),
                ending_cash_balance=round(w_end_balance, 2),
                has_deficit=has_def
            ))

        # Check for hidden shortage: Is total monthly inflow > total monthly outflow, yet daily closing dipped below 0?
        is_hidden_shortage = (total_inflows_acc > total_outflows_acc) and (earliest_shortfall is not None)

        return CashflowForecastHorizon(
            horizon_days=horizon_days,
            start_date=current_date,
            end_date=end_date,
            starting_cash=round(starting_cash, 2),
            projected_closing_cash=round(running_balance, 2),
            total_projected_inflows=round(total_inflows_acc, 2),
            total_projected_outflows=round(total_outflows_acc, 2),
            net_projected_cash_flow=round(total_inflows_acc - total_outflows_acc, 2),
            is_hidden_shortage_detected=is_hidden_shortage,
            earliest_shortfall_date=earliest_shortfall,
            peak_cash_deficit=round(peak_deficit, 2),
            daily_timeline=daily_records,
            weekly_timeline=weekly_records
        )

    @classmethod
    def generate_full_forecast_report(
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
        as_of_date: Optional[date] = None
    ) -> CashflowForecastReport:
        """
        Generates 30-day, 60-day, and 90-day forecasts from Financial Reality Engine inputs.
        Detects short-term liquidity shortages even when monthly total income > monthly expenses.
        """
        base_date = as_of_date or date.today()

        f30 = cls.generate_timeline(customer_id, starting_cash, transactions, loans, obligations, receivables, payables, 30, base_date)
        f60 = cls.generate_timeline(customer_id, starting_cash, transactions, loans, obligations, receivables, payables, 60, base_date)
        f90 = cls.generate_timeline(customer_id, starting_cash, transactions, loans, obligations, receivables, payables, 90, base_date)

        narrative = None
        if f30.is_hidden_shortage_detected:
            narrative = (
                f"CRITICAL TIMING MISMATCH DETECTED: While 30-day projected income (₹{f30.total_projected_inflows:,.0f}) "
                f"exceeds total outlays (₹{f30.total_projected_outflows:,.0f}), an acute cash collision occurs on "
                f"{f30.earliest_shortfall_date} due to NACH loan debits and fixed costs maturing before pending receivable inflows. "
                f"Peak intraday deficit reaches ₹{f30.peak_cash_deficit:,.0f}."
            )

        return CashflowForecastReport(
            customer_id=customer_id,
            customer_name=customer_name,
            archetype=archetype,
            as_of_date=base_date,
            current_cash=round(starting_cash, 2),
            minimum_required_cash=f30.daily_timeline[0].minimum_required_cash if f30.daily_timeline else 0.0,
            forecast_30d=f30,
            forecast_60d=f60,
            forecast_90d=f90,
            underlying_assumptions={
                "income_haircut_factor": 0.85,
                "conservative_forecasting": True,
                "prudential_cash_cushion_days": 21
            },
            hidden_shortage_narrative=narrative
        )
