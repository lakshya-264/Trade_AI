"""
Symbol Normalization Utility
Normalizes stock and index symbols for consistent API usage
"""

# Index symbol mappings to Yahoo Finance format
INDEX_SYMBOL_MAPPINGS = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "NIFTY_50": "^NSEI",
    "^NSEI": "^NSEI",
    "SENSEX": "^BSESN",
    "^BSESN": "^BSESN",
    "NIFTYBANK": "^NSEBANK",
    "NIFTY_BANK": "^NSEBANK",
    "BANKNIFTY": "^NSEBANK",
    "^NSEBANK": "^NSEBANK",
    "NIFTYIT": "^CNXIT",
    "NIFTY_IT": "^CNXIT",
    "^CNXIT": "^CNXIT",
    "NIFTYMIDCAP50": "^NSEMDCP50",
    "NIFTY_MIDCAP_50": "^NSEMDCP50",
    "NIFTYMIDCAP": "^NSEMDCP50",
    "^NSEMDCP50": "^NSEMDCP50",
    "NIFTYFIN": "^CNXFIN",
    "NIFTY_FIN": "^CNXFIN",
    "NIFTYFINANCIALSERVICES": "^CNXFIN",
    "NIFTY_FINANCIAL_SERVICES": "^CNXFIN",
    "^CNXFIN": "^CNXFIN",
    "BANKEX": "^BSE-BANKEX",
    "^BSE-BANKEX": "^BSE-BANKEX",
    # India VIX (Volatility Index)
    "INDIAVIX": "^INDIAVIX",
    "INDIA_VIX": "^INDIAVIX",
    "VIX": "^INDIAVIX",
    "^INDIAVIX": "^INDIAVIX",
}

# GIFT NIFTY symbol (futures contract traded on GIFT City exchange)
# GIFT NIFTY trades almost 24 hours and provides insights into next day opening
GIFT_NIFTY_SYMBOL = "NIFTY1!="  # Yahoo Finance symbol for GIFT NIFTY futures

# India VIX symbol
INDIA_VIX_SYMBOL = "^INDIAVIX"  # Yahoo Finance symbol for India VIX

def normalize_symbol_for_yahoo(symbol: str) -> str:
    """
    Normalize symbol to Yahoo Finance format
    - For indices: Use index mappings (e.g., NIFTY_50 -> ^NSEI)
    - For commodities/futures: Leave as-is (e.g., GC=F -> GC=F)
    - For stocks: Add .NS suffix (e.g., RELIANCE -> RELIANCE.NS)
    
    Returns the normalized symbol for Yahoo Finance API
    """
    if not symbol:
        return symbol
    
    original_symbol = symbol.upper().strip()
    
    # Check if it's an index
    if original_symbol in INDEX_SYMBOL_MAPPINGS:
        return INDEX_SYMBOL_MAPPINGS[original_symbol]
    
    # Check if it already has a suffix (.NS or ^)
    if symbol.endswith('.NS') or symbol.startswith('^'):
        return symbol
    
    # Check if it's a commodity/futures symbol (ends with =F, =X, etc.)
    # Yahoo Finance uses =F for futures, =X for currencies, etc.
    if '=' in symbol:
        return symbol
    
    # For stocks, add .NS suffix
    return f"{symbol}.NS"

def normalize_symbol_for_display(symbol: str) -> str:
    """
    Normalize symbol for display purposes
    Converts Yahoo Finance format back to user-friendly format
    """
    if not symbol:
        return symbol
    
    # Reverse mapping for display
    reverse_map = {v: k for k, v in INDEX_SYMBOL_MAPPINGS.items()}
    
    if symbol in reverse_map:
        # Return the first (most common) variant
        return reverse_map[symbol]
    
    # Remove .NS suffix for display
    if symbol.endswith('.NS'):
        return symbol[:-3]
    
    return symbol

def is_index_symbol(symbol: str) -> bool:
    """Check if symbol is an index"""
    if not symbol:
        return False
    return symbol.upper().strip() in INDEX_SYMBOL_MAPPINGS or symbol.startswith('^')

