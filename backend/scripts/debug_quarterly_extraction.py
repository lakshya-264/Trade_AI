"""
Debug Quarterly Extraction
Tests Screener.in quarterly data extraction for a specific stock
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.screener_scraper import screener_scraper
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_quarterly_extraction(symbol: str = "RELIANCE"):
    """Debug quarterly extraction for a specific stock"""
    logger.info(f"🔍 Debugging quarterly extraction for {symbol}...")
    
    try:
        # Fetch company data
        company_data = await screener_scraper.get_company_data(symbol, consolidated=True)
        
        logger.info(f"\n📊 Company Data Keys: {list(company_data.keys())}")
        
        # Check quarterly results
        quarterly_results = company_data.get("quarterly_results", [])
        logger.info(f"\n📅 Quarterly Results Count: {len(quarterly_results)}")
        
        if quarterly_results:
            logger.info(f"\n✅ Sample Quarterly Data:")
            for i, q in enumerate(quarterly_results[:3], 1):
                logger.info(f"  Quarter {i}: {q}")
        else:
            logger.warning(f"\n⚠️ No quarterly results found!")
            logger.info(f"\n🔍 Checking other data available:")
            logger.info(f"  - Key metrics: {bool(company_data.get('key_metrics'))}")
            logger.info(f"  - Growth metrics: {bool(company_data.get('growth_metrics'))}")
            logger.info(f"  - Balance sheet: {bool(company_data.get('balance_sheet'))}")
            logger.info(f"  - Cash flows: {bool(company_data.get('cash_flows'))}")
            logger.info(f"  - Shareholding: {bool(company_data.get('detailed_shareholding'))}")
        
        # Check if there's an error
        if "error" in company_data:
            logger.error(f"❌ Error: {company_data['error']}")
        
        return quarterly_results
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE"
    asyncio.run(debug_quarterly_extraction(symbol))


