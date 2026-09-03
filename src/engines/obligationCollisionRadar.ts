import { CustomerProfile } from '../types/models';

export interface DailyCashProjection {
  day: number;
  dateStr: string;
  projectedInflow: number;
  projectedOutflow: number;
  closingBalance: number;
  scheduledEvents: string[];
  isCollision: boolean;
}

export interface CollisionRadarReport {
  criticalLiquidityDate: string | null;
  daysUntilCollision: number | null;
  maximumProjectedShortfall: number;
  primaryCollisionCauses: string[];
  projections: DailyCashProjection[];
  summaryAlert: string;
}

/**
 * MODULE 4: Obligation Collision Radar (OCR) & Cash Runway
 * Maps day-level cash flow trajectories against fixed Indian statutory & NACH dates.
 * Identifies the exact critical day cash runs dry 15–45 days ahead.
 */
export class ObligationCollisionRadar {
  public static projectTrajectory(
    profile: CustomerProfile,
    horizonDays: number = 30,
    startDate: Date = new Date('2026-09-05')
  ): CollisionRadarReport {
    let currentBalance = profile.financialReality.currentLiquidBalance;
    const dailyProjections: DailyCashProjection[] = [];
    let criticalDate: string | null = null;
    let daysToCollision: number | null = null;
    let maxShortfall = 0;
    const collisionCauses: string[] = [];

    // Daily expected inflow (e.g. daily business collections or monthly salary arrival on the 1st)
    const dailyAverageInflow = profile.archetype === 'SALARIED' 
      ? 0 
      : Math.round(profile.financialReality.monthlyAverageIncome / 30);

    for (let i = 1; i <= horizonDays; i++) {
      const currentDate = new Date(startDate);
      currentDate.setDate(startDate.getDate() + (i - 1));
      const dayOfMonth = currentDate.getDate();
      const dateStr = currentDate.toISOString().split('T')[0];

      let dayInflow = dailyAverageInflow;
      let dayOutflow = 0;
      const events: string[] = [];

      // If Salaried, salary arrives on the 1st of month
      if (profile.archetype === 'SALARIED' && dayOfMonth === 1) {
        dayInflow += profile.financialReality.monthlyAverageIncome;
        events.push(`Salary Credit: +₹${profile.financialReality.monthlyAverageIncome.toLocaleString('en-IN')}`);
      }

      // Check scheduled loan NACH debits
      profile.loans.forEach(loan => {
        if (loan.nachDebitDate === dayOfMonth) {
          dayOutflow += loan.monthlyEmi;
          events.push(`NACH Debit (${loan.lenderName}): -₹${loan.monthlyEmi.toLocaleString('en-IN')}`);
        }
      });

      // Check fixed statutory/mandatory obligations (Rent, Payroll, GST, School Fee)
      profile.obligations.forEach(obl => {
        if (obl.dueDayOfMonth === dayOfMonth) {
          dayOutflow += obl.amount;
          events.push(`${obl.category}: -₹${obl.amount.toLocaleString('en-IN')}`);
        }
      });

      // Daily baseline living / operational burn
      const baseDailyBurn = Math.round(profile.financialReality.monthlyEssentialExpenses / 30);
      dayOutflow += baseDailyBurn;

      currentBalance = currentBalance + dayInflow - dayOutflow;
      const isCollision = currentBalance < 0;

      if (isCollision && !criticalDate) {
        criticalDate = dateStr;
        daysToCollision = i;
        collisionCauses.push(...events);
      }

      if (currentBalance < 0 && Math.abs(currentBalance) > maxShortfall) {
        maxShortfall = Math.abs(currentBalance);
      }

      dailyProjections.push({
        day: i,
        dateStr,
        projectedInflow: dayInflow,
        projectedOutflow: dayOutflow,
        closingBalance: currentBalance,
        scheduledEvents: events,
        isCollision
      });
    }

    const summaryAlert = criticalDate
      ? `Projected Liquidity Collision: ${criticalDate} (in ${daysToCollision} days). Projected maximum cash shortfall is ₹${maxShortfall.toLocaleString('en-IN')}.`
      : `No liquidity collision projected across the next ${horizonDays} days. Minimum projected buffer: ₹${Math.min(...dailyProjections.map(p => p.closingBalance)).toLocaleString('en-IN')}.`;

    return {
      criticalLiquidityDate: criticalDate,
      daysUntilCollision: daysToCollision,
      maximumProjectedShortfall: maxShortfall,
      primaryCollisionCauses: Array.from(new Set(collisionCauses)),
      projections: dailyProjections,
      summaryAlert
    };
  }
}
