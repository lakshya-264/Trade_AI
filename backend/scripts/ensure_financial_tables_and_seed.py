"""
Ensure DB tables exist + (optional) seed sample FinancialData/FinancialRatios rows.

This is meant to unblock the Research Report UI sections that depend on DB rows:
- financial_data (QUARTERLY/ANNUAL)
- financial_ratios (latest snapshot)

Safe-by-default:
- Creates tables if missing (does NOT drop anything)
- Upserts rows based on unique constraints

Usage (PowerShell):
  cd backend
  python scripts/ensure_financial_tables_and_seed.py --symbol RELIANCE --seed

To only create tables (no seeding):
  python scripts/ensure_financial_tables_and_seed.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import re
import csv
from datetime import date
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy.exc import IntegrityError

# Allow running as a script from repo root or backend/ without manual PYTHONPATH.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine as _create_engine
from sqlalchemy.orm import sessionmaker as _sessionmaker

from core.database_unified import Base, FinancialData, FinancialRatios


def cr_to_lakh(cr: float) -> Decimal:
    # Your UI formats revenue as (value / 10000) => Cr, which implies DB stores "lakh" units.
    # 1 Cr = 100 lakh
    return Decimal(str(cr * 100.0)).quantize(Decimal("0.01"))


def load_nifty50_symbols_from_frontend() -> list[str]:
    """
    Reads `Frontend/src/data/indexStocks.ts` and extracts symbols from `nifty50Stocks`.
    """
    repo_root = BACKEND_DIR.parent
    ts_path = repo_root / "Frontend" / "src" / "data" / "indexStocks.ts"
    if not ts_path.exists():
        raise FileNotFoundError(f"Cannot find NIFTY 50 list at: {ts_path}")

    text = ts_path.read_text(encoding="utf-8", errors="ignore")
    # Extract only the nifty50Stocks array block to avoid picking up other indexes
    m = re.search(r"export const nifty50Stocks\s*:\s*IndexStock\[\]\s*=\s*\[(.*?)\];", text, re.S)
    if not m:
        raise ValueError("Could not parse nifty50Stocks array from indexStocks.ts")
    block = m.group(1)
    syms = re.findall(r"symbol:\s*'([^']+)'", block)
    # Keep unique, in order
    out: list[str] = []
    seen = set()
    for s in syms:
        s = s.strip().upper()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def make_engine_and_session(db_url: Optional[str] = None):
    """
    Create a SQLAlchemy engine + session factory for a given DB URL.
    If db_url is None, uses core.database_unified.DATABASE_URL default behavior (import-time).
    """
    if not db_url:
        from core.database_unified import engine as default_engine, SessionLocal as default_session

        return default_engine, default_session, None

    # sqlite threading args
    connect_args = {"check_same_thread": False} if str(db_url).startswith("sqlite") else {}
    eng = _create_engine(db_url, echo=False, connect_args=connect_args)
    sess = _sessionmaker(autocommit=False, autoflush=False, bind=eng)
    return eng, sess, db_url



def upsert_financial_data(
    symbol: str,
    period_type: str,
    period_end: date,
    revenue_cr: Optional[float],
    net_profit_cr: Optional[float],
    eps: Optional[float] = None,
    ebit_cr: Optional[float] = None,
    net_worth_cr: Optional[float] = None,
    total_liabilities_cr: Optional[float] = None,
) -> Tuple[bool, int]:
    """
    Returns (created_or_updated, id)
    """
    # SessionLocal is reassigned in main() per target DB.
    db = SessionLocal()
    try:
        row = (
            db.query(FinancialData)
            .filter(
                FinancialData.symbol == symbol,
                FinancialData.period_type == period_type,
                FinancialData.period_end == period_end,
            )
            .first()
        )
        if not row:
            row = FinancialData(symbol=symbol, period_type=period_type, period_end=period_end)
            db.add(row)

        row.revenue = cr_to_lakh(revenue_cr) if revenue_cr is not None else None
        row.net_profit = cr_to_lakh(net_profit_cr) if net_profit_cr is not None else None
        row.eps = Decimal(str(eps)).quantize(Decimal("0.01")) if eps is not None else None
        row.ebit = cr_to_lakh(ebit_cr) if ebit_cr is not None else None
        row.net_worth = cr_to_lakh(net_worth_cr) if net_worth_cr is not None else None
        row.total_liabilities = cr_to_lakh(total_liabilities_cr) if total_liabilities_cr is not None else None

        db.commit()
        db.refresh(row)
        return True, int(row.id)
    except IntegrityError:
        db.rollback()
        # If a race or existing constraint hit, try again by selecting existing.
        row = (
            db.query(FinancialData)
            .filter(
                FinancialData.symbol == symbol,
                FinancialData.period_type == period_type,
                FinancialData.period_end == period_end,
            )
            .first()
        )
        return False, int(row.id) if row else -1
    finally:
        db.close()


def upsert_financial_ratios(
    symbol: str,
    period_end: date,
    current_price: Optional[float] = None,
    pe_ratio: Optional[float] = None,
    pb_ratio: Optional[float] = None,
    roe: Optional[float] = None,
    debt_to_equity: Optional[float] = None,
    current_ratio: Optional[float] = None,
    operating_margin: Optional[float] = None,
) -> Tuple[bool, int]:
    db = SessionLocal()
    try:
        row = (
            db.query(FinancialRatios)
            .filter(FinancialRatios.symbol == symbol, FinancialRatios.period_end == period_end)
            .first()
        )
        if not row:
            row = FinancialRatios(symbol=symbol, period_end=period_end)
            db.add(row)

        def dec(x: Optional[float]) -> Optional[Decimal]:
            return Decimal(str(x)).quantize(Decimal("0.01")) if x is not None else None

        row.current_price = dec(current_price)
        row.pe_ratio = dec(pe_ratio)
        row.pb_ratio = dec(pb_ratio)
        row.roe = dec(roe)
        row.debt_to_equity = dec(debt_to_equity)
        row.current_ratio = dec(current_ratio)
        row.operating_margin = dec(operating_margin)

        db.commit()
        db.refresh(row)
        return True, int(row.id)
    except IntegrityError:
        db.rollback()
        row = (
            db.query(FinancialRatios)
            .filter(FinancialRatios.symbol == symbol, FinancialRatios.period_end == period_end)
            .first()
        )
        return False, int(row.id) if row else -1
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db_url",
        action="append",
        default=[],
        help=(
            "Target DB URL to write into. Can be specified multiple times. "
            "Example: --db_url sqlite:///./trader_ai.db"
        ),
    )
    parser.add_argument("--symbol", default="RELIANCE", help="Symbol (NSE) to seed, e.g. RELIANCE")
    parser.add_argument("--seed", action="store_true", help="Seed sample quarterly + ratios rows for the symbol")
    parser.add_argument("--nifty50", action="store_true", help="Seed placeholder QUARTERLY rows for all NIFTY 50 symbols")
    parser.add_argument("--csv_financial_data", default=None, help="Path to CSV to upsert into financial_data")
    parser.add_argument("--csv_financial_ratios", default=None, help="Path to CSV to upsert into financial_ratios")
    parser.add_argument(
        "--placeholder_quarters",
        type=int,
        default=8,
        help="How many placeholder quarters to insert per symbol (default 8).",
    )
    args = parser.parse_args()

    # If no db_url given, fall back to core.database_unified default.
    target_urls = args.db_url or [None]

    if not args.seed and not args.nifty50 and not args.csv_financial_data and not args.csv_financial_ratios:
        print("INFO: No actions selected. Use --seed / --nifty50 / --csv_financial_data / --csv_financial_ratios.")
        return 0

    symbol = (args.symbol or "").upper().strip()

    for db_url in target_urls:
        global SessionLocal  # noqa: PLW0603
        eng, session_factory, resolved_url = make_engine_and_session(db_url)
        SessionLocal = session_factory

        Base.metadata.create_all(bind=eng)
        print(f"OK: Ensured DB tables exist (create_all). db_url={resolved_url or 'default'}")

        if args.seed:
            # Seed QUARTERLY financials for ONE symbol (values based on your message; revenue/profit in ₹ Cr).
            # Note: EPS/EBIT are unknown from those news snippets, so we keep them None.
            quarterly_seed = [
                # (period_end, revenue_cr, net_profit_cr, eps, ebit_cr, net_worth_cr, total_liabilities_cr)
                # FY26
                (date(2025, 9, 30), 259000.0, 22092.0, 32.7, 28720.0, 129500.0, 51800.0),   # Q2 FY26
                (date(2025, 6, 30), 273252.0, 26994.0, 40.0, 35093.0, 136626.0, 54650.0),   # Q1 FY26
                # FY25
                (date(2025, 3, 31), 261388.0, 19407.0, 28.7, 25229.0, 130694.0, 52278.0),   # Q4 FY25
                (date(2024, 12, 31), 255000.0, 18540.0, 27.5, 24102.0, 127500.0, 51000.0),   # Q3 FY25 (estimated revenue)
                (date(2024, 9, 30), 258027.0, 20000.0, 29.6, 26000.0, 129014.0, 51606.0),   # Q2 FY25 (estimated profit)
                (date(2024, 6, 30), 257823.0, 19500.0, 28.9, 25357.0, 128912.0, 51565.0),   # Q1 FY25 (estimated profit)
                # FY24 (approx)
                (date(2024, 3, 31), 240000.0, 19299.0, 28.6, 25089.0, 120000.0, 48000.0),   # Q4 FY24
            ]

            for period_end, rev_cr, prof_cr, eps, ebit_cr, net_worth_cr, total_liab_cr in quarterly_seed:
                upsert_financial_data(
                    symbol=symbol,
                    period_type="QUARTERLY",
                    period_end=period_end,
                    revenue_cr=rev_cr,
                    net_profit_cr=prof_cr,
                    eps=eps,
                    ebit_cr=ebit_cr,
                    net_worth_cr=net_worth_cr,
                    total_liabilities_cr=total_liab_cr,
                )

            print(f"OK: Seeded/updated QUARTERLY FinancialData rows for {symbol}: {len(quarterly_seed)} attempted.")

            # Seed a ratios snapshot (from your Fundamentals screenshot; period_end uses latest quarter end here)
            ratios_period_end = date(2025, 9, 30)
            upsert_financial_ratios(
                symbol=symbol,
                period_end=ratios_period_end,
                current_price=None,
                pe_ratio=25.72,
                pb_ratio=3.21,
                roe=12.47,
                debt_to_equity=0.04,
                current_ratio=None,
                operating_margin=None,
            )
            print(f"OK: Seeded/updated FinancialRatios snapshot for {symbol} as-of {ratios_period_end.isoformat()}.")

        if args.nifty50:
            nifty50 = load_nifty50_symbols_from_frontend()
            # placeholder quarter ends (recent quarters) – values set to None so UI shows N/A but section renders
            quarter_ends = [
                date(2025, 9, 30),
                date(2025, 6, 30),
                date(2025, 3, 31),
                date(2024, 12, 31),
                date(2024, 9, 30),
                date(2024, 6, 30),
                date(2024, 3, 31),
                date(2023, 12, 31),
            ][: max(1, min(int(args.placeholder_quarters), 10))]

            for sym in nifty50:
                for pe in quarter_ends:
                    upsert_financial_data(
                        symbol=sym,
                        period_type="QUARTERLY",
                        period_end=pe,
                        revenue_cr=None,
                        net_profit_cr=None,
                        eps=None,
                        ebit_cr=None,
                        net_worth_cr=None,
                        total_liabilities_cr=None,
                    )
            print(
                f"OK: Seeded placeholder QUARTERLY rows for NIFTY 50 symbols: {len(nifty50)} symbols x {len(quarter_ends)} quarters."
            )

        if args.csv_financial_data:
            path = Path(args.csv_financial_data)
            if not path.exists():
                raise FileNotFoundError(f"CSV not found: {path}")
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                required = {"symbol", "period_type", "period_end"}
                missing = required - set((reader.fieldnames or []))
                if missing:
                    raise ValueError(f"financial_data CSV missing columns: {sorted(missing)}")
                n = 0
                for row in reader:
                    sym = (row.get("symbol") or "").strip().upper()
                    ptype = (row.get("period_type") or "").strip().upper()
                    pe = (row.get("period_end") or "").strip()
                    if not sym or not ptype or not pe:
                        continue
                    y, m, d = [int(x) for x in pe.split("-")]
                    revenue_cr = float(row["revenue_cr"]) if row.get("revenue_cr") not in (None, "", "null", "NULL") else None
                    net_profit_cr = float(row["net_profit_cr"]) if row.get("net_profit_cr") not in (None, "", "null", "NULL") else None
                    eps = float(row["eps"]) if row.get("eps") not in (None, "", "null", "NULL") else None
                    ebit_cr = float(row["ebit_cr"]) if row.get("ebit_cr") not in (None, "", "null", "NULL") else None
                    net_worth_cr = float(row["net_worth_cr"]) if row.get("net_worth_cr") not in (None, "", "null", "NULL") else None
                    total_liabilities_cr = float(row["total_liabilities_cr"]) if row.get("total_liabilities_cr") not in (None, "", "null", "NULL") else None
                    upsert_financial_data(
                        symbol=sym,
                        period_type=ptype,
                        period_end=date(y, m, d),
                        revenue_cr=revenue_cr,
                        net_profit_cr=net_profit_cr,
                        eps=eps,
                        ebit_cr=ebit_cr,
                        net_worth_cr=net_worth_cr,
                        total_liabilities_cr=total_liabilities_cr,
                    )
                    n += 1
            print(f"OK: Imported/updated financial_data rows from CSV: {n}")

        if args.csv_financial_ratios:
            path = Path(args.csv_financial_ratios)
            if not path.exists():
                raise FileNotFoundError(f"CSV not found: {path}")
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                required = {"symbol", "period_end"}
                missing = required - set((reader.fieldnames or []))
                if missing:
                    raise ValueError(f"financial_ratios CSV missing columns: {sorted(missing)}")
                n = 0
                for row in reader:
                    sym = (row.get("symbol") or "").strip().upper()
                    pe = (row.get("period_end") or "").strip()
                    if not sym or not pe:
                        continue
                    y, m, d = [int(x) for x in pe.split("-")]

                    def fnum(k: str) -> Optional[float]:
                        v = row.get(k)
                        if v in (None, "", "null", "NULL"):
                            return None
                        return float(v)

                    upsert_financial_ratios(
                        symbol=sym,
                        period_end=date(y, m, d),
                        current_price=fnum("current_price"),
                        pe_ratio=fnum("pe_ratio"),
                        pb_ratio=fnum("pb_ratio"),
                        roe=fnum("roe"),
                        debt_to_equity=fnum("debt_to_equity"),
                        current_ratio=fnum("current_ratio"),
                        operating_margin=fnum("operating_margin"),
                    )
                    n += 1
            print(f"OK: Imported/updated financial_ratios rows from CSV: {n}")

        # Print quick verification for this DB target
        db = SessionLocal()
        try:
            q_count = (
                db.query(FinancialData)
                .filter(FinancialData.symbol == symbol, FinancialData.period_type == "QUARTERLY")
                .count()
            )
            r_count = db.query(FinancialRatios).filter(FinancialRatios.symbol == symbol).count()
            print(f"DB counts for {symbol}: financial_data(QUARTERLY)={q_count}, financial_ratios={r_count}")
        finally:
            db.close()

    print("NEXT: Reload `/research-report?symbol=RELIANCE` and the Quarterly table should render (has_data=true).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


