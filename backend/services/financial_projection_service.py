"""
Financial Projection + DCF + Sensitivity Service

Implements scenario-based (Base/Bull/Bear) 1-5 year projections for:
- Revenue, Net Profit, EPS, Free Cash Flow (approximated when missing)

Also produces:
- DCF intrinsic value band (per-share) by scenario
- Sensitivity grid (growth vs discount rate and terminal growth vs discount rate)

Notes:
- We do not have share count in current DB schema, so intrinsic value is computed on a
  per-share basis using EPS and a configurable EPS->FCF conversion ratio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from core.database_unified import FinancialData


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _cagr(start: float, end: float, years: int) -> Optional[float]:
    if years <= 0 or start is None or end is None:
        return None
    if start <= 0 or end <= 0:
        return None
    try:
        return (end / start) ** (1.0 / years) - 1.0
    except Exception:
        return None


def _pv(amount: float, rate: float, year: int) -> float:
    return amount / ((1.0 + rate) ** year)


@dataclass
class ScenarioConfig:
    name: str
    revenue_growth: float
    margin_delta: float
    discount_rate: float
    terminal_growth: float


class FinancialProjectionService:
    """
    Generates 5-year projections + DCF band + sensitivity.
    """

    def __init__(self):
        # Convert EPS to FCF/share when FCF is missing. Conservative default.
        self.default_eps_to_fcf = 0.85
        # Long-term margin mean reversion clamp
        self.min_profit_margin = 0.02
        self.max_profit_margin = 0.40

    def build_projections(
        self,
        db: Session,
        symbol: str,
        years: int = 5,
        base_discount_rate: float = 0.12,
        base_terminal_growth: float = 0.04,
        base_growth_override: Optional[float] = None,
        base_profit_margin_override: Optional[float] = None,
        bull_premium_growth: float = 0.03,
        bear_discount_growth: float = 0.03,
        bull_margin_delta: float = 0.01,
        bear_margin_delta: float = -0.01,
        eps_to_fcf: Optional[float] = None,
        sensitivity_discount_rates: Optional[List[float]] = None,
        sensitivity_terminal_growths: Optional[List[float]] = None,
        sensitivity_growth_rates: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        symbol = (symbol or "").upper().strip()
        years = max(1, min(int(years), 5))

        # Pull annual history (latest first)
        history = (
            db.query(FinancialData)
            .filter(FinancialData.symbol == symbol, FinancialData.period_type == "ANNUAL")
            .order_by(FinancialData.period_end.desc())
            .limit(10)
            .all()
        )
        
        # If no annual data, try to generate from quarterly data
        if not history:
            quarterly_data = (
                db.query(FinancialData)
                .filter(FinancialData.symbol == symbol, FinancialData.period_type == "QUARTERLY")
                .order_by(FinancialData.period_end.desc())
                .limit(20)  # Get last 20 quarters (5 years)
                .all()
            )
            
            if quarterly_data and len(quarterly_data) >= 4:
                # Group quarters by year and aggregate
                from collections import defaultdict
                from datetime import datetime
                
                annual_dict = defaultdict(lambda: {
                    'revenue': 0.0,
                    'net_profit': 0.0,
                    'net_worth': None,
                    'eps': None,
                    'ebit': 0.0,
                    'free_cash_flow': 0.0,
                    'period_end': None,
                    'count': 0
                })
                
                for q in quarterly_data:
                    if q.period_end:
                        year = q.period_end.year
                        annual_dict[year]['revenue'] += _safe_float(q.revenue) or 0.0
                        annual_dict[year]['net_profit'] += _safe_float(q.net_profit) or 0.0
                        annual_dict[year]['ebit'] += _safe_float(q.ebit) or 0.0
                        annual_dict[year]['free_cash_flow'] += _safe_float(q.free_cash_flow) or 0.0
                        # Use latest quarter's values for these (they're cumulative or point-in-time)
                        if annual_dict[year]['net_worth'] is None:
                            annual_dict[year]['net_worth'] = _safe_float(q.net_worth)
                        if annual_dict[year]['eps'] is None:
                            annual_dict[year]['eps'] = _safe_float(q.eps)
                        # Use latest period_end for the year
                        if annual_dict[year]['period_end'] is None:
                            annual_dict[year]['period_end'] = q.period_end
                        elif q.period_end and annual_dict[year]['period_end']:
                            if q.period_end > annual_dict[year]['period_end']:
                                annual_dict[year]['period_end'] = q.period_end
                        annual_dict[year]['count'] += 1
                
                # Convert to list of FinancialData-like objects (using a simple class)
                class AnnualData:
                    def __init__(self, year, data):
                        self.period_end = data['period_end'] or datetime(year, 12, 31).date()
                        self.revenue = data['revenue']
                        self.net_profit = data['net_profit']
                        self.net_worth = data['net_worth']
                        self.eps = data['eps']
                        self.ebit = data['ebit']
                        self.free_cash_flow = data['free_cash_flow']
                        self.period_type = "ANNUAL"
                
                # Create annual records (only years with at least 3 quarters)
                history = [
                    AnnualData(year, data) 
                    for year, data in sorted(annual_dict.items(), reverse=True)
                    if data['count'] >= 3  # At least 3 quarters to make a reasonable annual estimate
                ]
                
                if not history:
                    return {
                        "success": False,
                        "symbol": symbol,
                        "message": "No ANNUAL financial data found. Insufficient quarterly data to generate annual estimates. Please import/sync annual financials first.",
                    }
            else:
                return {
                    "success": False,
                    "symbol": symbol,
                    "message": "No ANNUAL financial data found. Insufficient quarterly data available. Please import/sync annual financials first.",
                }

        latest = history[0]
        # For CAGR, use oldest among available window
        oldest = history[-1]
        span_years = max(1, len(history) - 1)

        rev_latest = _safe_float(latest.revenue) or 0.0
        prof_latest = _safe_float(latest.net_profit) or 0.0
        eps_latest = _safe_float(latest.eps) or 0.0
        fcf_latest_total = _safe_float(getattr(latest, "free_cash_flow", None))

        # Historical margins/growth
        profit_margin_latest = (prof_latest / rev_latest) if rev_latest > 0 else 0.0
        profit_margin_latest = float(max(self.min_profit_margin, min(self.max_profit_margin, profit_margin_latest)))
        if base_profit_margin_override is not None:
            # override should be passed as decimal (e.g., 0.18 for 18%)
            profit_margin_latest = float(
                max(self.min_profit_margin, min(self.max_profit_margin, float(base_profit_margin_override)))
            )

        rev_old = _safe_float(oldest.revenue)
        prof_old = _safe_float(oldest.net_profit)
        eps_old = _safe_float(oldest.eps)

        rev_cagr = _cagr(rev_old, rev_latest, span_years)
        prof_cagr = _cagr(prof_old, prof_latest, span_years)
        eps_cagr = _cagr(eps_old, eps_latest, span_years)

        # Choose base growth: prefer revenue CAGR, else profit, else eps, else a conservative 8%
        base_growth = next(
            (g for g in [rev_cagr, prof_cagr, eps_cagr] if g is not None and 0 <= g <= 0.50),
            0.08,
        )
        if base_growth_override is not None:
            base_growth = float(max(0.01, min(0.30, float(base_growth_override))))

        # Approximate FCF/share baseline
        eps_to_fcf = float(eps_to_fcf if eps_to_fcf is not None else self.default_eps_to_fcf)
        fcf_per_share_base = None
        if fcf_latest_total is not None and eps_latest > 0:
            # We don't know shares outstanding, so keep per-share tied to EPS by conversion.
            # If we have total FCF but not shares, we still cannot compute per-share, so fallback.
            fcf_per_share_base = eps_latest * eps_to_fcf
        else:
            fcf_per_share_base = eps_latest * eps_to_fcf

        # Scenarios
        scenarios = [
            ScenarioConfig(
                name="base",
                revenue_growth=base_growth,
                margin_delta=0.0,
                discount_rate=base_discount_rate,
                terminal_growth=base_terminal_growth,
            ),
            ScenarioConfig(
                name="bull",
                revenue_growth=min(base_growth + bull_premium_growth, 0.30),
                margin_delta=bull_margin_delta,
                discount_rate=max(base_discount_rate - 0.01, 0.08),
                terminal_growth=min(base_terminal_growth + 0.01, 0.06),
            ),
            ScenarioConfig(
                name="bear",
                revenue_growth=max(base_growth - bear_discount_growth, 0.01),
                margin_delta=bear_margin_delta,
                discount_rate=min(base_discount_rate + 0.02, 0.18),
                terminal_growth=max(base_terminal_growth - 0.01, 0.02),
            ),
        ]

        def project_for_scenario(sc: ScenarioConfig) -> Dict[str, Any]:
            revenue = rev_latest
            margin = max(
                self.min_profit_margin,
                min(self.max_profit_margin, profit_margin_latest + sc.margin_delta),
            )
            eps = eps_latest
            fcfps = fcf_per_share_base

            rows: List[Dict[str, Any]] = []
            fcfps_stream: List[float] = []
            for y in range(1, years + 1):
                revenue = revenue * (1.0 + sc.revenue_growth)
                # keep margin stable with delta
                net_profit = revenue * margin
                # EPS growth tied to profit growth (simplified)
                eps = eps * (1.0 + sc.revenue_growth)
                fcfps = fcfps * (1.0 + sc.revenue_growth)
                rows.append(
                    {
                        "year": y,
                        "revenue": round(revenue, 2),
                        "net_profit": round(net_profit, 2),
                        "eps": round(eps, 2),
                        "fcf_per_share": round(fcfps, 4),
                        "profit_margin": round(margin * 100, 2),
                    }
                )
                fcfps_stream.append(float(fcfps))

            intrinsic = self._dcf_per_share(
                fcfps_stream=fcfps_stream,
                discount_rate=sc.discount_rate,
                terminal_growth=sc.terminal_growth,
            )
            return {
                "assumptions": {
                    "revenue_growth": sc.revenue_growth,
                    "profit_margin": margin,
                    "eps_to_fcf": eps_to_fcf,
                    "discount_rate": sc.discount_rate,
                    "terminal_growth": sc.terminal_growth,
                },
                "projection": rows,
                "dcf": intrinsic,
            }

        scenario_results = {sc.name: project_for_scenario(sc) for sc in scenarios}

        # Sensitivity defaults (pro-ish ranges)
        if sensitivity_discount_rates is None:
            sensitivity_discount_rates = [0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15]
        if sensitivity_terminal_growths is None:
            sensitivity_terminal_growths = [0.02, 0.03, 0.04, 0.05]
        if sensitivity_growth_rates is None:
            sensitivity_growth_rates = [max(base_growth - 0.02, 0.02), base_growth, min(base_growth + 0.02, 0.20)]

        base_fcfps_stream = [float(r["fcf_per_share"]) for r in scenario_results["base"]["projection"]]

        sensitivity_terminal_vs_discount = self._sensitivity_terminal_vs_discount(
            base_fcfps_stream, sensitivity_discount_rates, sensitivity_terminal_growths
        )
        sensitivity_growth_vs_discount = self._sensitivity_growth_vs_discount(
            fcfps0=fcf_per_share_base,
            years=years,
            growth_rates=sensitivity_growth_rates,
            discount_rates=sensitivity_discount_rates,
            terminal_growth=base_terminal_growth,
        )

        return {
            "success": True,
            "symbol": symbol,
            "as_of_period_end": latest.period_end.isoformat() if latest.period_end else None,
            "history_summary": {
                "revenue_latest": rev_latest,
                "net_profit_latest": prof_latest,
                "eps_latest": eps_latest,
                "profit_margin_latest": round(profit_margin_latest * 100, 2),
                "rev_cagr": rev_cagr,
                "profit_cagr": prof_cagr,
                "eps_cagr": eps_cagr,
                "base_growth_selected": base_growth,
            },
            "scenarios": scenario_results,
            "dcf_band": {
                "bear": scenario_results["bear"]["dcf"]["intrinsic_value_per_share"],
                "base": scenario_results["base"]["dcf"]["intrinsic_value_per_share"],
                "bull": scenario_results["bull"]["dcf"]["intrinsic_value_per_share"],
            },
            "sensitivity": {
                "terminal_growth_vs_discount": sensitivity_terminal_vs_discount,
                "growth_vs_discount": sensitivity_growth_vs_discount,
            },
        }

    def _dcf_per_share(self, fcfps_stream: List[float], discount_rate: float, terminal_growth: float) -> Dict[str, Any]:
        """
        Two-stage DCF on per-share free cash flow:
        PV(FCF_1..N) + PV(Terminal Value)
        Terminal Value = FCF_N * (1+g) / (r-g)
        """
        n = len(fcfps_stream)
        if n == 0:
            return {"intrinsic_value_per_share": 0.0, "pv_fcf": 0.0, "pv_terminal": 0.0}
        r = float(discount_rate)
        g = float(terminal_growth)
        if r <= g:
            # Avoid division by zero / negative terminal.
            g = max(0.0, r - 0.01)
        pv_fcf = sum(_pv(f, r, year=i + 1) for i, f in enumerate(fcfps_stream))
        terminal_value = (fcfps_stream[-1] * (1.0 + g)) / max(1e-6, (r - g))
        pv_terminal = _pv(terminal_value, r, n)
        intrinsic = pv_fcf + pv_terminal
        return {
            "intrinsic_value_per_share": round(float(intrinsic), 2),
            "pv_fcf": round(float(pv_fcf), 2),
            "pv_terminal": round(float(pv_terminal), 2),
            "discount_rate": r,
            "terminal_growth": g,
            "projection_years": n,
        }

    def _sensitivity_terminal_vs_discount(
        self,
        base_fcfps_stream: List[float],
        discount_rates: List[float],
        terminal_growths: List[float],
    ) -> Dict[str, Any]:
        grid: List[Dict[str, Any]] = []
        for g in terminal_growths:
            row = {"terminal_growth": g, "values": []}
            for r in discount_rates:
                row["values"].append(
                    self._dcf_per_share(base_fcfps_stream, r, g)["intrinsic_value_per_share"]
                )
            grid.append(row)
        return {"discount_rates": discount_rates, "rows": grid}

    def _sensitivity_growth_vs_discount(
        self,
        fcfps0: float,
        years: int,
        growth_rates: List[float],
        discount_rates: List[float],
        terminal_growth: float,
    ) -> Dict[str, Any]:
        grid: List[Dict[str, Any]] = []
        for gr in growth_rates:
            stream = []
            f = float(fcfps0)
            for i in range(1, years + 1):
                f *= (1.0 + gr)
                stream.append(f)
            row = {"growth_rate": gr, "values": []}
            for r in discount_rates:
                row["values"].append(self._dcf_per_share(stream, r, terminal_growth)["intrinsic_value_per_share"])
            grid.append(row)
        return {"discount_rates": discount_rates, "rows": grid}


financial_projection_service = FinancialProjectionService()


