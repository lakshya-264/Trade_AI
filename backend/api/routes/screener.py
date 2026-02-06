"""
Stock Screener API Routes
Scan and filter stocks based on technical criteria
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
import logging
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import aiohttp
import re
from bs4 import BeautifulSoup

from utils.symbol_utils import clean_symbol, normalize_yahoo_symbol, is_valid_symbol
from sqlalchemy.orm import Session

from core.database import get_db
from core.database_unified import FinancialData, ScreenerBalanceSheet
from core.nse_bse_stock_scraper import nse_bse_scraper

logger = logging.getLogger(__name__)
router = APIRouter()


_latest_results_cache: Dict[str, Tuple[datetime, Dict[str, Any]]] = {}


def _parse_screener_date(value: str) -> Optional[str]:
    try:
        v = (value or "").strip()
        if not v:
            return None

        v = re.sub(r"\s+", " ", v)

        for fmt in ["%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d-%B-%Y"]:
            try:
                dt = datetime.strptime(v, fmt)
                return dt.date().isoformat()
            except Exception:
                pass

        return None
    except Exception:
        return None


def _extract_symbol_from_company_link(href: str) -> Optional[str]:
    try:
        if not href:
            return None
        m = re.search(r"/company/([^/]+)/?", href)
        if not m:
            return None
        sym = (m.group(1) or "").strip().upper()
        return sym or None
    except Exception:
        return None


async def _fetch_screener_latest_results() -> List[Dict[str, Any]]:
    url = "https://www.screener.in/latest-results/"
    home_url = "https://www.screener.in/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.screener.in/",
    }

    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        # Prime cookies (Screener often expects a session from homepage)
        try:
            async with session.get(home_url, allow_redirects=True) as _:
                pass
        except Exception:
            pass

        last_status: Optional[int] = None
        last_body_snippet: Optional[str] = None
        # Retry with light backoff for transient blocks / rate limits
        for attempt in range(3):
            async with session.get(url, allow_redirects=True) as resp:
                last_status = resp.status
                if resp.status == 200:
                    html = await resp.text()
                    break

                try:
                    body = await resp.text()
                    last_body_snippet = (body or "")[:200]
                except Exception:
                    last_body_snippet = None

                if resp.status in (403, 429, 503):
                    await asyncio.sleep(0.8 * (2 ** attempt))
                    continue

                raise HTTPException(status_code=503, detail=f"Screener.in returned HTTP {resp.status}")
        else:
            html = None

    # Optional Playwright fallback if aiohttp is blocked
    if not html:
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                html = await page.content()
                await browser.close()
        except Exception:
            status_part = f"HTTP {last_status}" if last_status else "unknown status"
            extra = f" ({last_body_snippet})" if last_body_snippet else ""
            raise HTTPException(status_code=503, detail=f"Screener.in blocked or unavailable: {status_part}{extra}")

    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        return []

    header_cells = table.find_all("th")
    header = [re.sub(r"\s+", " ", (th.get_text(" ") or "").strip()).lower() for th in header_cells]

    def find_col(*candidates: str) -> Optional[int]:
        for cand in candidates:
            for i, h in enumerate(header):
                if cand in h:
                    return i
        return None

    company_col = find_col("company")
    date_col = find_col("date", "result")
    quarter_col = find_col("quarter", "period")

    rows: List[Dict[str, Any]] = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue

        cells_text = [re.sub(r"\s+", " ", (td.get_text(" ") or "").strip()) for td in tds]

        company_name = None
        company_url = None
        symbol = None

        try:
            company_td = tds[company_col] if company_col is not None and company_col < len(tds) else tds[0]
            a = company_td.find("a")
            if a:
                company_name = (a.get_text(" ") or "").strip() or None
                company_url = a.get("href")
                symbol = _extract_symbol_from_company_link(company_url)
            else:
                company_name = (company_td.get_text(" ") or "").strip() or None
        except Exception:
            pass

        result_date = None
        if date_col is not None and date_col < len(cells_text):
            result_date = _parse_screener_date(cells_text[date_col])

        quarter = None
        if quarter_col is not None and quarter_col < len(cells_text):
            quarter = cells_text[quarter_col] or None

        if not company_name and not symbol:
            continue

        rows.append({
            "symbol": symbol,
            "company_name": company_name,
            "company_url": company_url,
            "result_date": result_date,
            "quarter": quarter,
            "raw": cells_text,
        })

    return rows

# NSE Top 50 stocks for screening (Fixed symbol names)
NSE_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
    "ICICIBANK", "KOTAKBANK", "SBIN", "BHARTIARTL", "BAJFINANCE",
    "ITC", "ASIANPAINT", "HCLTECH", "AXISBANK", "LT",
    "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND",
    "WIPRO", "ONGC", "NTPC", "POWERGRID", "M&M",
    "TATASTEEL", "JSWSTEEL", "INDUSINDBK", "ADANIPOWER", "COALINDIA",
    "BAJAJFINSV", "TECHM", "GRASIM", "HINDALCO", "DIVISLAB",
    "DRREDDY", "CIPLA", "EICHERMOT", "APOLLOHOSP", "HEROMOTOCO",
    "BRITANNIA", "SHREECEM", "UPL", "TATAMOTORS", "BAJAJ-AUTO",
    "BPCL", "IOC", "ADANIPORTS", "TATACONSUM", "VEDL"
]


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _pct_change(current: Optional[float], base: Optional[float]) -> Optional[float]:
    if current is None or base is None:
        return None
    if base == 0:
        return None
    try:
        return ((current - base) / abs(base)) * 100.0
    except Exception:
        return None


def _find_yoy_row(rows_desc: List[FinancialData], latest: FinancialData) -> Optional[FinancialData]:
    """Try to find same-month previous-year row; fallback to ~4 quarters back if available."""
    try:
        target_year = latest.period_end.year - 1
        target_month = latest.period_end.month
        for r in rows_desc:
            if r.period_end.year == target_year and r.period_end.month == target_month:
                return r
        if len(rows_desc) >= 5:
            return rows_desc[4]
    except Exception:
        return None
    return None


@router.get("/nifty50-results")
async def nifty50_results_screener(
    profit_yoy_up: bool = Query(True, description="Net profit YoY increased"),
    revenue_yoy_up: bool = Query(True, description="Revenue YoY increased"),
    revenue_qoq_up: bool = Query(False, description="Revenue QoQ increased"),
    margin_yoy_up: bool = Query(False, description="EBIT margin YoY increased"),
    debt_down: bool = Query(False, description="Debt (borrowings) decreased YoY"),
    db: Session = Depends(get_db),
):
    """Nifty 50 results-style screener computed from stored financial tables."""
    try:
        results: List[Dict[str, Any]] = []

        for symbol in NSE_STOCKS:
            sym = (symbol or "").upper().strip()
            if not sym:
                continue

            q_rows: List[FinancialData] = (
                db.query(FinancialData)
                .filter(FinancialData.symbol == sym, FinancialData.period_type == "QUARTERLY")
                .order_by(FinancialData.period_end.desc())
                .limit(12)
                .all()
            )

            if not q_rows:
                continue

            latest = q_rows[0]
            prev = q_rows[1] if len(q_rows) >= 2 else None
            yoy = _find_yoy_row(q_rows, latest)

            latest_rev = _safe_float(latest.revenue)
            prev_rev = _safe_float(prev.revenue) if prev else None
            yoy_rev = _safe_float(yoy.revenue) if yoy else None

            latest_profit = _safe_float(latest.net_profit)
            prev_profit = _safe_float(prev.net_profit) if prev else None
            yoy_profit = _safe_float(yoy.net_profit) if yoy else None

            rev_yoy_pct = _pct_change(latest_rev, yoy_rev)
            rev_qoq_pct = _pct_change(latest_rev, prev_rev)
            profit_yoy_pct = _pct_change(latest_profit, yoy_profit)

            # EBIT margin proxy (EBIT / Revenue)
            latest_ebit = _safe_float(latest.ebit)
            yoy_ebit = _safe_float(yoy.ebit) if yoy else None
            latest_margin = (latest_ebit / latest_rev * 100.0) if latest_ebit is not None and latest_rev not in (None, 0) else None
            yoy_margin = (yoy_ebit / yoy_rev * 100.0) if yoy_ebit is not None and yoy_rev not in (None, 0) else None
            margin_yoy_delta = (latest_margin - yoy_margin) if latest_margin is not None and yoy_margin is not None else None

            # Debt proxy from ScreenerBalanceSheet.borrowings
            bs_rows: List[ScreenerBalanceSheet] = (
                db.query(ScreenerBalanceSheet)
                .filter(ScreenerBalanceSheet.symbol == sym)
                .order_by(ScreenerBalanceSheet.period_end.desc())
                .limit(8)
                .all()
            )
            latest_debt = _safe_float(bs_rows[0].borrowings) if bs_rows else None
            yoy_debt_row = None
            if bs_rows and len(bs_rows) > 1:
                target_year = bs_rows[0].period_end.year - 1
                target_month = bs_rows[0].period_end.month
                for r in bs_rows:
                    if r.period_end.year == target_year and r.period_end.month == target_month:
                        yoy_debt_row = r
                        break
                if yoy_debt_row is None:
                    yoy_debt_row = bs_rows[1]
            yoy_debt = _safe_float(yoy_debt_row.borrowings) if yoy_debt_row else None
            debt_yoy_pct = _pct_change(latest_debt, yoy_debt)

            flags = {
                "profit_yoy_up": profit_yoy_pct is not None and profit_yoy_pct > 0,
                "revenue_yoy_up": rev_yoy_pct is not None and rev_yoy_pct > 0,
                "revenue_qoq_up": rev_qoq_pct is not None and rev_qoq_pct > 0,
                "margin_yoy_up": margin_yoy_delta is not None and margin_yoy_delta > 0,
                "debt_down": latest_debt is not None and yoy_debt is not None and latest_debt < yoy_debt,
            }

            # Apply requested filters
            if profit_yoy_up and not flags["profit_yoy_up"]:
                continue
            if revenue_yoy_up and not flags["revenue_yoy_up"]:
                continue
            if revenue_qoq_up and not flags["revenue_qoq_up"]:
                continue
            if margin_yoy_up and not flags["margin_yoy_up"]:
                continue
            if debt_down and not flags["debt_down"]:
                continue

            reasons: List[str] = []
            if flags["profit_yoy_up"]:
                reasons.append("Net Profit YoY ↑")
            if flags["revenue_yoy_up"]:
                reasons.append("Revenue YoY ↑")
            if flags["revenue_qoq_up"]:
                reasons.append("Revenue QoQ ↑")
            if flags["margin_yoy_up"]:
                reasons.append("EBIT Margin YoY ↑")
            if flags["debt_down"]:
                reasons.append("Debt ↓")

            results.append({
                "symbol": sym,
                "latest_quarter": latest.period_end.isoformat() if latest.period_end else None,
                "metrics": {
                    "revenue_latest": latest_rev,
                    "revenue_prev_q": prev_rev,
                    "revenue_yoy": yoy_rev,
                    "revenue_yoy_pct": rev_yoy_pct,
                    "revenue_qoq_pct": rev_qoq_pct,
                    "net_profit_latest": latest_profit,
                    "net_profit_yoy": yoy_profit,
                    "net_profit_yoy_pct": profit_yoy_pct,
                    "ebit_margin_latest": latest_margin,
                    "ebit_margin_yoy": yoy_margin,
                    "ebit_margin_yoy_delta": margin_yoy_delta,
                    "debt_latest": latest_debt,
                    "debt_yoy": yoy_debt,
                    "debt_yoy_pct": debt_yoy_pct,
                },
                "flags": flags,
                "reasons": reasons,
            })

        return {
            "success": True,
            "data": {
                "total": len(results),
                "results": results,
                "universe": "NIFTY50",
            },
            "message": f"Results screener returned {len(results)} stocks",
        }
    except Exception as e:
        logger.error(f"Error in nifty50_results_screener: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nse-results")
async def nse_results_screener(
    q: Optional[str] = Query(None, description="Optional search term (symbol contains)"),
    profit_yoy_up: bool = Query(True, description="Net profit YoY increased"),
    revenue_yoy_up: bool = Query(True, description="Revenue YoY increased"),
    revenue_qoq_up: bool = Query(False, description="Revenue QoQ increased"),
    margin_yoy_up: bool = Query(False, description="EBIT margin YoY increased"),
    debt_down: bool = Query(False, description="Debt (borrowings) decreased YoY"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Rows per page"),
    db: Session = Depends(get_db),
):
    """All-NSE results-style screener computed from stored financial tables (paginated)."""
    try:
        nse_list = await nse_bse_scraper.get_nse_stock_list()
        symbols_all: List[str] = [
            (s.get("symbol") or "").strip().upper() for s in (nse_list or []) if (s.get("symbol") or "").strip()
        ]

        if q:
            q_u = q.strip().upper()
            symbols_all = [s for s in symbols_all if q_u in s]

        total_universe = len(symbols_all)
        start = (page - 1) * page_size
        end = start + page_size
        symbols_page = symbols_all[start:end]

        results: List[Dict[str, Any]] = []
        for sym in symbols_page:
            q_rows: List[FinancialData] = (
                db.query(FinancialData)
                .filter(FinancialData.symbol == sym, FinancialData.period_type == "QUARTERLY")
                .order_by(FinancialData.period_end.desc())
                .limit(12)
                .all()
            )

            if not q_rows:
                continue

            latest = q_rows[0]
            prev = q_rows[1] if len(q_rows) >= 2 else None
            yoy = _find_yoy_row(q_rows, latest)

            latest_rev = _safe_float(latest.revenue)
            prev_rev = _safe_float(prev.revenue) if prev else None
            yoy_rev = _safe_float(yoy.revenue) if yoy else None

            latest_profit = _safe_float(latest.net_profit)
            prev_profit = _safe_float(prev.net_profit) if prev else None
            yoy_profit = _safe_float(yoy.net_profit) if yoy else None

            rev_yoy_pct = _pct_change(latest_rev, yoy_rev)
            rev_qoq_pct = _pct_change(latest_rev, prev_rev)
            profit_yoy_pct = _pct_change(latest_profit, yoy_profit)

            latest_ebit = _safe_float(latest.ebit)
            yoy_ebit = _safe_float(yoy.ebit) if yoy else None
            latest_margin = (latest_ebit / latest_rev * 100.0) if latest_ebit is not None and latest_rev not in (None, 0) else None
            yoy_margin = (yoy_ebit / yoy_rev * 100.0) if yoy_ebit is not None and yoy_rev not in (None, 0) else None
            margin_yoy_delta = (latest_margin - yoy_margin) if latest_margin is not None and yoy_margin is not None else None

            bs_rows: List[ScreenerBalanceSheet] = (
                db.query(ScreenerBalanceSheet)
                .filter(ScreenerBalanceSheet.symbol == sym)
                .order_by(ScreenerBalanceSheet.period_end.desc())
                .limit(8)
                .all()
            )
            latest_debt = _safe_float(bs_rows[0].borrowings) if bs_rows else None
            yoy_debt_row = None
            if bs_rows and len(bs_rows) > 1:
                target_year = bs_rows[0].period_end.year - 1
                target_month = bs_rows[0].period_end.month
                for r in bs_rows:
                    if r.period_end.year == target_year and r.period_end.month == target_month:
                        yoy_debt_row = r
                        break
                if yoy_debt_row is None:
                    yoy_debt_row = bs_rows[1]
            yoy_debt = _safe_float(yoy_debt_row.borrowings) if yoy_debt_row else None
            debt_yoy_pct = _pct_change(latest_debt, yoy_debt)

            flags = {
                "profit_yoy_up": profit_yoy_pct is not None and profit_yoy_pct > 0,
                "revenue_yoy_up": rev_yoy_pct is not None and rev_yoy_pct > 0,
                "revenue_qoq_up": rev_qoq_pct is not None and rev_qoq_pct > 0,
                "margin_yoy_up": margin_yoy_delta is not None and margin_yoy_delta > 0,
                "debt_down": latest_debt is not None and yoy_debt is not None and latest_debt < yoy_debt,
            }

            if profit_yoy_up and not flags["profit_yoy_up"]:
                continue
            if revenue_yoy_up and not flags["revenue_yoy_up"]:
                continue
            if revenue_qoq_up and not flags["revenue_qoq_up"]:
                continue
            if margin_yoy_up and not flags["margin_yoy_up"]:
                continue
            if debt_down and not flags["debt_down"]:
                continue

            reasons: List[str] = []
            if flags["profit_yoy_up"]:
                reasons.append("Net Profit YoY ↑")
            if flags["revenue_yoy_up"]:
                reasons.append("Revenue YoY ↑")
            if flags["revenue_qoq_up"]:
                reasons.append("Revenue QoQ ↑")
            if flags["margin_yoy_up"]:
                reasons.append("EBIT Margin YoY ↑")
            if flags["debt_down"]:
                reasons.append("Debt ↓")

            results.append({
                "symbol": sym,
                "latest_quarter": latest.period_end.isoformat() if latest.period_end else None,
                "metrics": {
                    "revenue_latest": latest_rev,
                    "revenue_prev_q": prev_rev,
                    "revenue_yoy": yoy_rev,
                    "revenue_yoy_pct": rev_yoy_pct,
                    "revenue_qoq_pct": rev_qoq_pct,
                    "net_profit_latest": latest_profit,
                    "net_profit_yoy": yoy_profit,
                    "net_profit_yoy_pct": profit_yoy_pct,
                    "ebit_margin_latest": latest_margin,
                    "ebit_margin_yoy": yoy_margin,
                    "ebit_margin_yoy_delta": margin_yoy_delta,
                    "debt_latest": latest_debt,
                    "debt_yoy": yoy_debt,
                    "debt_yoy_pct": debt_yoy_pct,
                },
                "flags": flags,
                "reasons": reasons,
            })

        total_pages = (total_universe + page_size - 1) // page_size if page_size else 1

        return {
            "success": True,
            "data": {
                "total": len(results),
                "results": results,
                "universe": "NSE",
                "page": page,
                "page_size": page_size,
                "total_universe": total_universe,
                "total_pages": total_pages,
                "q": q,
            },
            "message": f"NSE results screener returned {len(results)} stocks",
        }
    except Exception as e:
        logger.error(f"Error in nse_results_screener: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest-results")
async def latest_results(ttl_minutes: int = Query(30, ge=1, le=240)):
    try:
        now = datetime.utcnow()
        cache_key = "latest-results"
        cached = _latest_results_cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]

        try:
            rows = await _fetch_screener_latest_results()
            payload = {
                "success": True,
                "data": {
                    "rows": rows,
                    "source": "screener.in/latest-results",
                },
                "message": f"Fetched {len(rows)} rows",
            }
            expires = now + timedelta(minutes=max(1, min(ttl_minutes, 240)))
            _latest_results_cache[cache_key] = (expires, payload)
            return payload
        except HTTPException as e:
            # If scrape fails but we have cached data (even stale), return stale data.
            if cached:
                stale_payload = cached[1]
                stale_payload = {
                    **stale_payload,
                    "message": (stale_payload.get("message") or "") + f" (stale cache served; live fetch failed: {e.detail})",
                }
                return stale_payload
            raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in latest_results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ScreenerRequest(BaseModel):
    """Stock screening criteria"""
    # Price filters
    min_price: Optional[float] = Field(None, description="Minimum price")
    max_price: Optional[float] = Field(None, description="Maximum price")
    min_volume: Optional[int] = Field(None, description="Minimum volume")
    min_change_percent: Optional[float] = Field(None, description="Minimum price change %")
    max_change_percent: Optional[float] = Field(None, description="Maximum price change %")
    
    # Technical filters
    min_rsi: Optional[float] = Field(None, description="Minimum RSI")
    max_rsi: Optional[float] = Field(None, description="Maximum RSI")
    price_above_sma: Optional[int] = Field(None, description="Price above SMA (e.g., 200)")
    macd_bullish: Optional[bool] = Field(None, description="MACD bullish crossover")
    near_52w_high: Optional[bool] = Field(None, description="Near 52-week high")
    
    # Financial ratio filters
    max_pe_ratio: Optional[float] = Field(None, description="Maximum PE ratio")
    min_pe_ratio: Optional[float] = Field(None, description="Minimum PE ratio")
    min_roe: Optional[float] = Field(None, description="Minimum ROE %")
    max_debt_to_equity: Optional[float] = Field(None, description="Maximum Debt-to-Equity")
    min_profit_growth: Optional[float] = Field(None, description="Minimum Profit Growth %")
    min_revenue_growth: Optional[float] = Field(None, description="Minimum Revenue Growth %")
    
    # General filters
    symbols: Optional[List[str]] = Field(None, description="Specific symbols to scan")
    sectors: Optional[List[str]] = Field(None, description="Filter by sectors")
    min_market_cap: Optional[float] = Field(None, description="Minimum market cap")
    max_market_cap: Optional[float] = Field(None, description="Maximum market cap")
    sort_by: Optional[str] = Field("volume", description="Sort field")
    limit: Optional[int] = Field(50, description="Max results")

class StockResult(BaseModel):
    """Screener result for a stock"""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    avg_volume: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    rsi: Optional[float] = None
    signal: Optional[str] = None  # "BUY", "SELL", "HOLD"

@router.get("/health")
async def health_check():
    """Health check"""
    return {
        "success": True,
        "service": "screener",
        "status": "healthy",
        "available_stocks": len(NSE_STOCKS)
    }

@router.post("/scan")
async def scan_stocks(criteria: ScreenerRequest) -> Dict:
    """
    Scan stocks based on criteria
    
    Returns list of stocks matching the filters
    """
    try:
        logger.info(f"🔍 Scanning stocks with criteria: {criteria.dict()}")
        
        # Use provided symbols or default to NSE top 50
        symbols_to_scan = criteria.symbols or NSE_STOCKS
        
        results = []
        
        for symbol in symbols_to_scan[:criteria.limit]:
            try:
                # Clean and normalize symbol using utility function
                cleaned = clean_symbol(symbol)
                if not is_valid_symbol(cleaned):
                    logger.warning(f"⚠️ Skipping invalid symbol: {symbol}")
                    continue
                
                # Normalize for Yahoo Finance
                yf_symbol = normalize_yahoo_symbol(cleaned, exchange="NS")
                
                # Fetch stock data
                ticker = yf.Ticker(yf_symbol)
                
                # Try to get info, skip if fails
                try:
                    info = ticker.info
                    if not info or len(info) == 0:
                        logger.warning(f"⚠️ No info for {cleaned}, skipping")
                        continue
                except Exception as info_error:
                    logger.warning(f"⚠️ Could not fetch info for {cleaned}: {info_error}")
                    continue
                
                # Get recent price data
                try:
                    hist = ticker.history(period="5d")
                    if hist.empty:
                        logger.warning(f"⚠️ No price data for {cleaned}, skipping")
                        continue
                except Exception as hist_error:
                    logger.warning(f"⚠️ Could not fetch history for {cleaned}: {hist_error}")
                    continue
                
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                volume = int(hist['Volume'].iloc[-1])
                
                change = current_price - prev_close
                change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                
                # Apply filters
                if criteria.min_price and current_price < criteria.min_price:
                    continue
                if criteria.max_price and current_price > criteria.max_price:
                    continue
                if criteria.min_volume and volume < criteria.min_volume:
                    continue
                if criteria.min_change_percent and change_percent < criteria.min_change_percent:
                    continue
                if criteria.max_change_percent and change_percent > criteria.max_change_percent:
                    continue
                
                # Calculate simple RSI
                rsi = calculate_rsi(hist['Close'].values) if len(hist) >= 14 else None
                
                # Get financial ratios from database if available
                from core.database_unified import FinancialRatios, SessionLocal as ScreenerDB
                db = ScreenerDB()
                try:
                    latest_ratios = db.query(FinancialRatios).filter(
                        FinancialRatios.symbol == symbol
                    ).order_by(FinancialRatios.period_end.desc()).first()
                    
                    pe_ratio = float(latest_ratios.pe_ratio) if latest_ratios and latest_ratios.pe_ratio else info.get('trailingPE')
                    roe = float(latest_ratios.roe) if latest_ratios and latest_ratios.roe else None
                    debt_to_equity = float(latest_ratios.debt_to_equity) if latest_ratios and latest_ratios.debt_to_equity else None
                    profit_growth = float(latest_ratios.profit_growth_5y) if latest_ratios and latest_ratios.profit_growth_5y else None
                    revenue_growth = float(latest_ratios.revenue_growth_5y) if latest_ratios and latest_ratios.revenue_growth_5y else None
                except:
                    pe_ratio = info.get('trailingPE')
                    roe = None
                    debt_to_equity = None
                    profit_growth = None
                    revenue_growth = None
                finally:
                    db.close()
                
                # Calculate SMA
                sma_20 = hist['Close'].rolling(20).mean().iloc[-1] if len(hist) >= 20 else None
                sma_50 = hist['Close'].rolling(50).mean().iloc[-1] if len(hist) >= 50 else None
                sma_200 = hist['Close'].rolling(200).mean().iloc[-1] if len(hist) >= 200 else None
                
                # Get 52-week high/low
                year_high = hist['High'].max() if len(hist) > 0 else current_price
                year_low = hist['Low'].min() if len(hist) > 0 else current_price
                near_52w_high = ((current_price - year_low) / (year_high - year_low)) > 0.9 if year_high > year_low else False
                
                # Calculate MACD
                macd_bullish = False
                if len(hist) >= 26:
                    ema_12 = hist['Close'].ewm(span=12).mean()
                    ema_26 = hist['Close'].ewm(span=26).mean()
                    macd_line = ema_12 - ema_26
                    signal_line = macd_line.ewm(span=9).mean()
                    macd_bullish = macd_line.iloc[-1] > signal_line.iloc[-1]
                
                # Get market cap
                market_cap = info.get('marketCap')
                
                # Apply market cap filters
                if criteria.min_market_cap and (market_cap is None or market_cap < criteria.min_market_cap):
                    continue
                if criteria.max_market_cap and (market_cap is None or market_cap > criteria.max_market_cap):
                    continue
                
                # Apply financial ratio filters
                if criteria.min_roe and (roe is None or roe < criteria.min_roe):
                    continue
                if criteria.max_pe_ratio and (pe_ratio is None or pe_ratio > criteria.max_pe_ratio):
                    continue
                if criteria.min_pe_ratio and (pe_ratio is None or pe_ratio < criteria.min_pe_ratio):
                    continue
                if criteria.max_debt_to_equity and (debt_to_equity is None or debt_to_equity > criteria.max_debt_to_equity):
                    continue
                if criteria.min_profit_growth and (profit_growth is None or profit_growth < criteria.min_profit_growth):
                    continue
                if criteria.min_revenue_growth and (revenue_growth is None or revenue_growth < criteria.min_revenue_growth):
                    continue
                
                # Apply technical filters
                if criteria.min_rsi and (rsi is None or rsi < criteria.min_rsi):
                    continue
                if criteria.max_rsi and (rsi is None or rsi > criteria.max_rsi):
                    continue
                if criteria.price_above_sma:
                    if criteria.price_above_sma == 200 and (sma_200 is None or current_price <= sma_200):
                        continue
                    elif criteria.price_above_sma == 50 and (sma_50 is None or current_price <= sma_50):
                        continue
                    elif criteria.price_above_sma == 20 and (sma_20 is None or current_price <= sma_20):
                        continue
                if criteria.macd_bullish and not macd_bullish:
                    continue
                if criteria.near_52w_high and not near_52w_high:
                    continue
                
                # Determine signal
                signal = "HOLD"
                if rsi:
                    if rsi < 30:
                        signal = "BUY"
                    elif rsi > 70:
                        signal = "SELL"
                
                # Add to results
                results.append({
                    "symbol": cleaned,  # Use cleaned symbol
                    "name": info.get('longName', cleaned),
                    "price": round(current_price, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "volume": volume,
                    "avg_volume": info.get('averageVolume'),
                    "market_cap": market_cap,
                    "sector": info.get('sector', 'N/A'),
                    "pe_ratio": round(pe_ratio, 2) if pe_ratio else None,
                    "rsi": round(rsi, 2) if rsi else None,
                    "roe": round(roe, 2) if roe else None,
                    "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity else None,
                    "profit_growth": round(profit_growth, 2) if profit_growth else None,
                    "revenue_growth": round(revenue_growth, 2) if revenue_growth else None,
                    "sma_20": round(sma_20, 2) if sma_20 else None,
                    "sma_50": round(sma_50, 2) if sma_50 else None,
                    "sma_200": round(sma_200, 2) if sma_200 else None,
                    "year_high": round(year_high, 2),
                    "year_low": round(year_low, 2),
                    "signal": signal
                })
                
            except Exception as e:
                # Log as warning instead of error for delisted/invalid symbols
                error_msg = str(e).lower()
                cleaned_symbol = clean_symbol(symbol) if symbol else "UNKNOWN"
                if "delisted" in error_msg or "no data found" in error_msg or "404" in error_msg:
                    logger.warning(f"⚠️ Symbol {cleaned_symbol} may be delisted or invalid: {e}")
                else:
                    logger.error(f"❌ Error scanning {cleaned_symbol}: {e}")
                continue
        
        # Apply sector filter if specified
        if criteria.sectors:
            results = [r for r in results if r.get("sector") in criteria.sectors]
        
        # Sort results
        sort_field_map = {
            "volume": "volume",
            "change": "change_percent",
            "price": "price",
            "rsi": "rsi",
            "pe_ratio": "pe_ratio",
            "roe": "roe",
            "profit_growth": "profit_growth"
        }
        sort_field = sort_field_map.get(criteria.sort_by, "volume")
        results.sort(key=lambda x: x.get(sort_field, 0) or 0, reverse=True)
        
        logger.info(f"✅ Found {len(results)} stocks matching criteria")
        
        return {
            "success": True,
            "count": len(results),
            "results": results,
            "scanned": len(symbols_to_scan)
        }
        
    except Exception as e:
        logger.error(f"Error in stock screener: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presets/{preset_name}")
async def get_preset(preset_name: str) -> Dict:
    """
    Get predefined screening preset
    
    Available presets:
    - high_volume: High trading volume
    - breakouts: Price breakouts (>5% up)
    - oversold: RSI < 30
    - overbought: RSI > 70
    - gainers: Top gainers today
    - losers: Top losers today
    """
    presets = {
        "high_volume": ScreenerRequest(
            min_volume=1000000,
            sort_by="volume",
            limit=20
        ),
        "breakouts": ScreenerRequest(
            min_change_percent=5.0,
            sort_by="change",
            limit=20
        ),
        "oversold": ScreenerRequest(
            max_rsi=30,
            sort_by="rsi",
            limit=20
        ),
        "overbought": ScreenerRequest(
            min_rsi=70,
            sort_by="rsi",
            limit=20
        ),
        "value_stocks": ScreenerRequest(
            max_pe_ratio=20,
            min_roe=15,
            sort_by="pe_ratio",
            limit=20
        ),
        "growth_stocks": ScreenerRequest(
            min_profit_growth=15,
            sort_by="profit_growth",
            limit=20
        ),
        "low_debt": ScreenerRequest(
            max_debt_to_equity=0.5,
            sort_by="debt_to_equity",
            limit=20
        ),
        "above_sma200": ScreenerRequest(
            price_above_sma=200,
            sort_by="price",
            limit=20
        ),
        "gainers": ScreenerRequest(
            min_change_percent=2.0,
            sort_by="change",
            limit=20
        ),
        "losers": ScreenerRequest(
            max_change_percent=-2.0,
            sort_by="change",
            limit=20
        )
    }
    
    if preset_name not in presets:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
    
    return await scan_stocks(presets[preset_name])

def calculate_rsi(prices: np.ndarray, period: int = 14) -> Optional[float]:
    """Calculate RSI indicator"""
    try:
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    except:
        return None

