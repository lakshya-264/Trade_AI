"""
Financial Data Parser Service
Parses PDF/Excel files to extract financial data
100% Legal - Parsing public documents
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class FinancialDataParser:
    """Parse financial data from PDF/Excel files"""
    
    def __init__(self):
        pass
    
    def parse_pdf(self, pdf_content: bytes, symbol: str) -> Optional[Dict]:
        """
        Parse financial data from PDF
        
        Args:
            pdf_content: PDF file content as bytes
            symbol: Stock symbol
        
        Returns:
            Dictionary with extracted financial data
        """
        try:
            # Try to import pdfplumber or PyPDF2
            try:
                import pdfplumber
                
                financial_data = {
                    "symbol": symbol,
                    "period_type": "ANNUAL",  # Will be determined from content
                    "period_end": None,
                    "revenue": None,
                    "net_profit": None,
                    "net_worth": None,
                    "total_assets": None,
                    "total_liabilities": None,
                    "current_assets": None,
                    "current_liabilities": None,
                    "eps": None,
                    "book_value": None,
                    "ebit": None,
                    "capital_employed": None,
                    "free_cash_flow": None,
                    "filing_date": None
                }
                
                # Parse PDF
                with pdfplumber.open(pdf_content) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                
                # Extract financial data using regex patterns
                financial_data = self._extract_from_text(text, financial_data)
                
                logger.info(f"✅ Parsed financial data for {symbol}")
                return financial_data
            
            except ImportError:
                logger.warning("pdfplumber not installed. Install with: pip install pdfplumber")
                return None
        
        except Exception as e:
            logger.error(f"Error parsing PDF for {symbol}: {e}")
            return None
    
    def parse_excel(self, excel_content: bytes, symbol: str) -> Optional[Dict]:
        """
        Parse financial data from Excel file
        
        Args:
            excel_content: Excel file content as bytes
            symbol: Stock symbol
        
        Returns:
            Dictionary with extracted financial data
        """
        try:
            import pandas as pd
            from io import BytesIO
            
            financial_data = {
                "symbol": symbol,
                "period_type": "QUARTERLY",
                "period_end": None,
                "revenue": None,
                "net_profit": None,
                "net_worth": None,
                "total_assets": None,
                "total_liabilities": None,
                "current_assets": None,
                "current_liabilities": None,
                "eps": None,
                "book_value": None,
                "ebit": None,
                "capital_employed": None,
                "free_cash_flow": None,
                "filing_date": None
            }
            
            # Read Excel
            df = pd.read_excel(BytesIO(excel_content))
            
            # Extract data from Excel (simplified - actual implementation would be more complex)
            # Look for common column names
            for col in df.columns:
                col_lower = str(col).lower()
                
                if "revenue" in col_lower or "sales" in col_lower:
                    financial_data["revenue"] = self._extract_numeric(df[col].iloc[-1])
                elif "profit" in col_lower and "net" in col_lower:
                    financial_data["net_profit"] = self._extract_numeric(df[col].iloc[-1])
                elif "net worth" in col_lower or "shareholders" in col_lower:
                    financial_data["net_worth"] = self._extract_numeric(df[col].iloc[-1])
            
            logger.info(f"✅ Parsed Excel financial data for {symbol}")
            return financial_data
        
        except Exception as e:
            logger.error(f"Error parsing Excel for {symbol}: {e}")
            return None
    
    def _extract_from_text(self, text: str, financial_data: Dict) -> Dict:
        """Extract financial data from text using regex"""
        try:
            # Patterns to find financial data
            patterns = {
                "revenue": [
                    r"Total\s+Revenue[:\s]+([\d,]+\.?\d*)",
                    r"Revenue[:\s]+([\d,]+\.?\d*)",
                    r"Sales[:\s]+([\d,]+\.?\d*)"
                ],
                "net_profit": [
                    r"Net\s+Profit[:\s]+([\d,]+\.?\d*)",
                    r"Profit\s+After\s+Tax[:\s]+([\d,]+\.?\d*)"
                ],
                "net_worth": [
                    r"Net\s+Worth[:\s]+([\d,]+\.?\d*)",
                    r"Shareholders'\s+Equity[:\s]+([\d,]+\.?\d*)"
                ],
                "eps": [
                    r"Earnings\s+Per\s+Share[:\s]+([\d,]+\.?\d*)",
                    r"EPS[:\s]+([\d,]+\.?\d*)"
                ]
            }
            
            for key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        value = self._extract_numeric(match.group(1))
                        if value:
                            financial_data[key] = value
                            break
            
            return financial_data
        
        except Exception as e:
            logger.error(f"Error extracting from text: {e}")
            return financial_data
    
    def _extract_numeric(self, value) -> Optional[float]:
        """Extract numeric value from string"""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                # Remove commas and convert
                cleaned = re.sub(r'[,\s]', '', str(value))
                # Remove currency symbols
                cleaned = re.sub(r'[₹$€£]', '', cleaned)
                return float(cleaned) if cleaned else None
            
            return None
        
        except (ValueError, TypeError):
            return None

# Create singleton instance
financial_data_parser = FinancialDataParser()

