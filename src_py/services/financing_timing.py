"""
Financing Timing Engine Service.
Determines WHEN credit is most appropriate (e.g. BORROW_NOW vs BORROW_LATER).
Specifically addresses scenarios such as:
- Business currently in weak seasonal revenue trough, but historical data predicts strong recovery in 2 months.
  Evaluating: "Would delaying borrowing reduce long-term debt pressure?"
- Large pending receivables arriving in 10-14 days -> USE_RECEIVABLE_FINANCING.
- High pre-existing debt burden -> RESTRUCTURE_EXISTING_DEBT or AVOID_BORROWING.
- Immediate working capital demand with stable forward cash flow -> BORROW_NOW or LIMITED_BORROWING.
Outputs:
- recommended_timing, recommended_amount, reason, confidence.
"""
from typing import Dict, Any, Optional
from datetime import datetime

from src_py.models.financing_timing_schemas import (
    FinancingTimingOption, FinancingTimingReport
)
from src_py.models.schemas import FinancialRealityObject
from src_py.models.seasonal_schemas import SeasonalForecastReport
from src_py.models.receivable_schemas import ReceivablesAnalysisReport


class FinancingTimingEngineService:

    @classmethod
    def evaluate_financing_timing(
        cls,
        business_id: str,
        fre: FinancialRealityObject,
        seasonal_forecast: Optional[SeasonalForecastReport] = None,
        receivables_report: Optional[ReceivablesAnalysisReport] = None,
        proposed_amount: float = 500000.0
    ) -> FinancingTimingReport:
        """
        Determines the optimal timing and quantum for credit deployment.
        """
        dsr_pct = fre.debt_service_ratio.value * 100.0
        fcf = fre.free_cash_flow.value
        buffer_d = fre.cash_buffer_days.value
        monthly_income = max(1.0, fre.monthly_income.value)

        # 1. Inspect Seasonal Profile: Is business currently in a trough with imminent surge?
        is_in_seasonal_trough = False
        surge_in_months = 0
        surge_month_name = None

        if seasonal_forecast and seasonal_forecast.monthly_forecasts:
            forecasts = seasonal_forecast.monthly_forecasts
            first_m = forecasts[0]
            if first_m.seasonal_index < 1.0:
                is_in_seasonal_trough = True
                # Find the first month where seasonal_index rises materially (> 1.05)
                for idx, m in enumerate(forecasts[1:], start=1):
                    if m.seasonal_index >= 1.05 and idx <= 4:
                        surge_in_months = idx
                        surge_month_name = m.month_label
                        break

        # 2. Inspect Receivable Profile: Can receivables bridge the gap?
        rec_14d = receivables_report.expected_14_day_cash if receivables_report else 0.0
        rec_covers_majority = (rec_14d >= proposed_amount * 0.70) if proposed_amount > 0 else False

        # 3. Decision Matrix

        # Scenario A: High pre-existing debt burden (> 48% DSR)
        if dsr_pct >= 48.0:
            timing = FinancingTimingOption.RESTRUCTURE_EXISTING_DEBT
            amt = 0.0
            window = 0
            opt_window = "Immediate Debt Restructuring"
            reason = (
                f"Existing debt service ratio is already elevated at {dsr_pct:.1f}%. "
                f"Adding incremental debt will compound debt pressure. "
                f"Priority Action: Restructure existing amortization schedules under RBI MSME framework before seeking new credit."
            )
            conf = 0.94

        # Scenario B: High-confidence receivables can cover immediate needs
        elif rec_covers_majority and rec_14d > 0:
            timing = FinancingTimingOption.USE_RECEIVABLE_FINANCING
            amt = round(min(proposed_amount, rec_14d), 2)
            window = 0
            opt_window = "Immediate (TReDS / Invoice Acceleration)"
            reason = (
                f"Outstanding high/moderate confidence receivables of ₹{rec_14d:,.0f} are expected within 14 days. "
                f"Recommendation: Utilize non-debt receivable financing (e.g. TReDS discounting) to cover near-term cash needs "
                f"without incurring multi-year interest and amortization drag."
            )
            conf = 0.93

        # Scenario C: Currently in seasonal trough, strong revenue surge in 2 months (Specification Example!)
        elif is_in_seasonal_trough and surge_in_months in [1, 2, 3, 4, 5]:
            timing = FinancingTimingOption.BORROW_LATER
            amt = proposed_amount * 0.75  # Smaller bridge or waiting
            window = surge_in_months
            opt_window = f"In {surge_in_months} month(s) ({surge_month_name or 'Post-Trough'})"
            reason = (
                f"Business is currently experiencing a temporary seasonal demand trough. "
                f"Historical patterns indicate strong revenue recovery in {surge_in_months} month(s) ({surge_month_name or 'peak season'}). "
                f"Delaying borrowing until revenues rebound will reduce long-term debt pressure, avoid taking debt at depressed cash flows, "
                f"and qualify the business for higher borrowing power at lower risk."
            )
            conf = 0.91

        # Scenario D: Extremely low buffer and negative FCF without imminent seasonal recovery
        elif buffer_d < 7 and fcf < -50000.0 and not is_in_seasonal_trough:
            timing = FinancingTimingOption.AVOID_BORROWING
            amt = 0.0
            window = 0
            opt_window = "Not Recommended"
            reason = (
                f"Cash buffer is depleted ({buffer_d} days) and operating cash flow is running at -₹{abs(fcf):,.0f}/mo. "
                f"Taking term debt without addressing structural operational burn will accelerate default risk. "
                f"Action: Implement operational expense reduction and equity/working capital triage."
            )
            conf = 0.92

        # Scenario E: Moderate leverage (DSR 35-45%) -> LIMITED_BORROWING
        elif dsr_pct > 35.0:
            timing = FinancingTimingOption.LIMITED_BORROWING
            max_safe = max(50000.0, (monthly_income * 0.35 - fre.monthly_debt_service.value) * 18.0)
            amt = round(min(proposed_amount, max_safe), 2)
            window = 0
            opt_window = "Immediate (Capped Quantum)"
            reason = (
                f"Current DSR of {dsr_pct:.1f}% allows for restricted borrowing. "
                f"Borrowing is approved with strict limit of ₹{amt:,.0f} to ensure total debt service does not breach prudential limits."
            )
            conf = 0.88

        # Scenario F: Healthy fundamentals -> BORROW_NOW
        else:
            timing = FinancingTimingOption.BORROW_NOW
            amt = proposed_amount
            window = 0
            opt_window = "Immediate"
            reason = (
                f"Operating cash flows are stable, cash buffer is healthy ({buffer_d} days), and debt service ratio ({dsr_pct:.1f}%) "
                f"is comfortably within the safe borrowing envelope. Borrowing now to fund growth or capital expenditure is sustainable."
            )
            conf = 0.95

        return FinancingTimingReport(
            business_id=business_id,
            recommended_timing=timing,
            recommended_amount=amt,
            recommended_window_months=window,
            optimal_timing_window=opt_window,
            reason=reason,
            confidence=conf,
            current_season_status="Seasonal Trough" if is_in_seasonal_trough else "Normal Operating Season",
            upcoming_recovery_month=surge_month_name,
            expected_receivable_inflow_14d=round(rec_14d, 2),
            existing_debt_service_ratio=round(dsr_pct, 1)
        )
