"""
Test Report Generation
Tests research report generation for a sample stock to verify data is working
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database_unified import SessionLocal, StockMaster, FinancialData, FinancialRatios
from services.comprehensive_report_generator import comprehensive_report_generator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test with a few stocks
TEST_STOCKS = ["RELIANCE", "TCS", "HDFCBANK", "INFY"]

def check_database_data(db: Session, symbol: str):
    """Check what data exists in database for a symbol"""
    logger.info(f"\n📊 Checking database data for {symbol}...")
    
    # Check StockMaster
    stock = db.query(StockMaster).filter(StockMaster.symbol == symbol.upper()).first()
    if stock:
        logger.info(f"  ✅ StockMaster: {stock.company_name}")
    else:
        logger.warning(f"  ⚠️ StockMaster: Not found")
    
    # Check FinancialData
    financial_data = db.query(FinancialData).filter(
        FinancialData.symbol == symbol.upper()
    ).count()
    logger.info(f"  📊 FinancialData records: {financial_data}")
    
    quarterly_data = db.query(FinancialData).filter(
        FinancialData.symbol == symbol.upper(),
        FinancialData.period_type == "QUARTERLY"
    ).count()
    logger.info(f"  📅 Quarterly records: {quarterly_data}")
    
    annual_data = db.query(FinancialData).filter(
        FinancialData.symbol == symbol.upper(),
        FinancialData.period_type == "ANNUAL"
    ).count()
    logger.info(f"  📅 Annual records: {annual_data}")
    
    # Check FinancialRatios
    ratios = db.query(FinancialRatios).filter(
        FinancialRatios.symbol == symbol.upper()
    ).count()
    logger.info(f"  📈 FinancialRatios records: {ratios}")
    
    return {
        "has_stock": stock is not None,
        "financial_data_count": financial_data,
        "quarterly_count": quarterly_data,
        "annual_count": annual_data,
        "ratios_count": ratios
    }

async def test_report_generation(symbol: str):
    """Test report generation for a symbol"""
    logger.info(f"\n🧪 Testing report generation for {symbol}...")
    
    db = SessionLocal()
    try:
        # Check database data first
        data_status = check_database_data(db, symbol)
        
        if not data_status["has_stock"]:
            logger.warning(f"⚠️ {symbol} not in StockMaster, skipping...")
            return False
        
        # Generate report
        logger.info(f"📝 Generating research report for {symbol}...")
        report = await comprehensive_report_generator.generate_comprehensive_report(
            symbol=symbol,
            db=db
        )
        
        # Report generator returns the report dict directly, not wrapped in success
        if report and isinstance(report, dict) and report.get("symbol"):
            logger.info(f"✅ Report generated successfully for {symbol}")
            
            # Check report sections
            sections = report.get("sections", {})
            logger.info(f"  📑 Report sections: {len(sections)}")
            
            # Check key sections
            key_sections = [
                "executive_summary", "key_metrics", "quarterly_pl", 
                "yearly_pl", "financial_ratios", "financial_strength"
            ]
            
            for section_name in key_sections:
                section = sections.get(section_name, {})
                has_data = section.get("has_data", False) if isinstance(section, dict) else bool(section)
                status = "✅" if has_data else "⚠️"
                logger.info(f"  {status} {section_name}: {has_data}")
            
            return True
        else:
            logger.error(f"❌ Failed to generate report for {symbol}")
            logger.error(f"   Report type: {type(report)}")
            logger.error(f"   Report keys: {list(report.keys()) if isinstance(report, dict) else 'N/A'}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing report for {symbol}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()

async def main():
    """Main test function"""
    logger.info("🧪 Starting Report Generation Test")
    logger.info("=" * 60)
    
    results = []
    
    for symbol in TEST_STOCKS:
        success = await test_report_generation(symbol)
        results.append({"symbol": symbol, "success": success})
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    successful = sum(1 for r in results if r["success"])
    for result in results:
        status = "✅" if result["success"] else "❌"
        logger.info(f"{status} {result['symbol']}")
    
    logger.info(f"\n✅ Successful: {successful}/{len(TEST_STOCKS)}")
    logger.info("=" * 60)
    
    return successful == len(TEST_STOCKS)

if __name__ == "__main__":
    import asyncio
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

