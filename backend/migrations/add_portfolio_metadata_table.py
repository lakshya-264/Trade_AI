"""
Migration script to add portfolio_metadata table
This table stores portfolio information (name, description, initial allocation)
"""
import sqlite3
import os
import sys

# Get database path
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'trader_ai.db')

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    sys.exit(1)

print(f"Connecting to database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if portfolio_metadata table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='portfolio_metadata'")
    if cursor.fetchone():
        print("[INFO] portfolio_metadata table already exists")
    else:
        # Create portfolio_metadata table
        cursor.execute('''
        CREATE TABLE portfolio_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            total_value REAL DEFAULT 0.0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # Create index on user_id for faster queries
        cursor.execute('CREATE INDEX idx_portfolio_metadata_user_id ON portfolio_metadata(user_id)')
        
        conn.commit()
        print("[OK] Created portfolio_metadata table")
        print("[OK] Created index on user_id")
    
    # Verify table structure
    cursor.execute("PRAGMA table_info(portfolio_metadata)")
    columns = cursor.fetchall()
    print(f"\nportfolio_metadata table structure:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    # Check if there are any existing portfolios
    cursor.execute("SELECT COUNT(*) FROM portfolio_metadata")
    count = cursor.fetchone()[0]
    print(f"\nExisting portfolio_metadata records: {count}")
    
except Exception as e:
    print(f"[ERROR] Error: {e}")
    conn.rollback()
    sys.exit(1)
finally:
    conn.close()

print("\n[SUCCESS] Migration completed successfully!")

