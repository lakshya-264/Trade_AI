"""
Compatibility shim re-exporting unified database constructs.
This satisfies imports like `from .database import ...`.
"""

from .database_unified import (  # noqa: F401
    Base,
    SessionLocal,
    engine,
    init_db,
    get_db,
    # models
    User,
    MarketData,
    Portfolio,
    Order,
    PerformanceMetrics,
    ChatSession,
    ChatMessage,
    OTPVerification,
    Alert,
    AlertTrigger,
    SmartMoneyVolumeActivity,
    Watchlist,
    PaperAccount,
    PaperOrder,
    PaperPosition,
)

"""
Database configuration - imports from unified database
"""

from .database_unified import *
