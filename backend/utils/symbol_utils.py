"""
Symbol Utilities
Universal functions for cleaning and normalizing stock symbols
"""

import re
from typing import Optional

# Common symbol corrections mapping
SYMBOL_CORRECTIONS = {
    "ADANIPOWERS": "ADANIPOWER",
    "COAL INDIA": "COALINDIA",
    "$ADANIPOWERS": "ADANIPOWER",
    "$COAL INDIA": "COALINDIA",
    "COALINDIA": "COALINDIA",  # Already correct
    "ADANIPOWER": "ADANIPOWER",  # Already correct
}

def clean_symbol(symbol: str) -> str:
    """
    Clean and normalize a stock symbol for Yahoo Finance
    
    Removes:
    - Leading/trailing whitespace
    - Dollar signs ($)
    - Spaces
    - Common typos
    
    Args:
        symbol: Raw symbol string (e.g., "$ADANIPOWERS", "COAL INDIA")
    
    Returns:
        Cleaned symbol (e.g., "ADANIPOWER", "COALINDIA")
    """
    if not symbol:
        return ""
    
    # Convert to string and strip whitespace
    clean = str(symbol).strip().upper()
    
    # Remove dollar signs
    clean = clean.replace("$", "")
    
    # Remove spaces
    clean = clean.replace(" ", "")
    
    # Apply known corrections
    if clean in SYMBOL_CORRECTIONS:
        clean = SYMBOL_CORRECTIONS[clean]
    
    # Remove any remaining special characters except hyphens (for symbols like BAJAJ-AUTO)
    clean = re.sub(r'[^A-Z0-9\-]', '', clean)
    
    return clean

def normalize_yahoo_symbol(symbol: str, exchange: str = "NS") -> str:
    """
    Normalize symbol for Yahoo Finance API
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE", "RELIANCE.NS")
        exchange: Exchange suffix (default: "NS" for NSE)
    
    Returns:
        Normalized Yahoo Finance symbol (e.g., "RELIANCE.NS")
    """
    clean = clean_symbol(symbol)
    
    if not clean:
        return ""
    
    # If already has .NS or .BO suffix, keep it
    if clean.endswith(".NS") or clean.endswith(".BO"):
        return clean
    
    # Add exchange suffix
    return f"{clean}.{exchange}"

def is_valid_symbol(symbol: str) -> bool:
    """
    Check if a symbol is valid (non-empty after cleaning)
    
    Args:
        symbol: Stock symbol to validate
    
    Returns:
        True if symbol is valid, False otherwise
    """
    cleaned = clean_symbol(symbol)
    return bool(cleaned and len(cleaned) > 0)

