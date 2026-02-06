"""
Update existing FinancialData rows with placeholder values for:
- ebit (for operating margin calculation)
- net_worth (for debt-to-equity calculation)
- total_liabilities (for debt-to-equity calculation)
- eps (if missing)

This script estimates these values based on revenue and net_profit where available.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy.orm import sessionmaker
from core.database_unified import engine, FinancialData
from decimal import Decimal

SessionLocal = sessionmaker(bind=engine)

def cr_to_lakh(cr: float) -> Decimal:
    """Convert Crore to Lakh (DB stores in Lakhs)."""
    return Decimal(str(cr * 100.0)).quantize(Decimal("0.01"))

def update_financial_data():
    """Update existing FinancialData rows with estimated values."""
    db = SessionLocal()
    try:
        # Get all quarterly rows
        rows = db.query(FinancialData).filter(
            FinancialData.period_type == "QUARTERLY"
        ).all()
        
        updated_count = 0
        for row in rows:
            updated = False
            
            # Estimate EBIT if we have revenue and net_profit
            # EBIT ≈ Net Profit + Interest + Taxes
            # For estimation: EBIT ≈ Net Profit * 1.3 (rough approximation)
            if row.revenue and row.net_profit and not row.ebit:
                estimated_ebit_cr = float(row.net_profit) / 100.0 * 1.3  # Convert lakh to cr, then estimate
                row.ebit = cr_to_lakh(estimated_ebit_cr)
                updated = True
            
            # Estimate EPS if we have net_profit
            # EPS = Net Profit / Shares Outstanding
            # For RELIANCE: ~67.5 Cr shares outstanding
            # For other stocks, use a rough estimate
            if row.net_profit and not row.eps:
                net_profit_cr = float(row.net_profit) / 100.0  # Convert lakh to cr
                # Rough estimate: assume 50-100 Cr shares for large caps
                shares_estimate = 50.0 if "RELIANCE" not in row.symbol else 67.5
                estimated_eps = net_profit_cr / shares_estimate
                row.eps = Decimal(str(estimated_eps)).quantize(Decimal("0.01"))
                updated = True
            
            # Estimate Net Worth and Total Liabilities for debt-to-equity
            # Net Worth ≈ Revenue * 0.5 (rough estimate for asset-heavy companies)
            # Total Liabilities ≈ Net Worth * 0.4 (rough estimate for D/E ≈ 0.4)
            if row.revenue and not row.net_worth:
                revenue_cr = float(row.revenue) / 100.0  # Convert lakh to cr
                estimated_net_worth_cr = revenue_cr * 0.5
                row.net_worth = cr_to_lakh(estimated_net_worth_cr)
                updated = True
                
                if not row.total_liabilities:
                    # D/E ratio ≈ 0.4 means liabilities ≈ net_worth * 0.4
                    estimated_liabilities_cr = estimated_net_worth_cr * 0.4
                    row.total_liabilities = cr_to_lakh(estimated_liabilities_cr)
                    updated = True
            
            if updated:
                updated_count += 1
        
        db.commit()
        print(f"OK: Updated {updated_count} rows with estimated values")
        print("   - EBIT estimated from net_profit")
        print("   - EPS estimated from net_profit")
        print("   - Net Worth and Total Liabilities estimated from revenue")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        return 1
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(update_financial_data())




