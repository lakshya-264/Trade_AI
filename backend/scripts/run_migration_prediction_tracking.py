"""
Run migration to create prediction tracking tables
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from migrations.create_prediction_tracking_tables import create_prediction_tracking_tables

if __name__ == "__main__":
    print("Creating prediction tracking tables...")
    create_prediction_tracking_tables()
    print("✅ Migration completed!")
