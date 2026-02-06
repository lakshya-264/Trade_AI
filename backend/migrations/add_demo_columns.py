"""
Migration script to add demo_cash_balance, real_cash_balance to users table
and is_demo to orders table
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
    # Check current users table structure
    cursor.execute("PRAGMA table_info(users)")
    users_cols = [col[1] for col in cursor.fetchall()]
    print(f"\nCurrent users table columns: {users_cols}")
    
    # Add demo_cash_balance if it doesn't exist
    if 'demo_cash_balance' not in users_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN demo_cash_balance REAL DEFAULT 1000000.0")
            print("✅ Added demo_cash_balance column to users table")
        except Exception as e:
            print(f"❌ Error adding demo_cash_balance: {e}")
    else:
        print("ℹ️ demo_cash_balance column already exists")
    
    # Add real_cash_balance if it doesn't exist
    if 'real_cash_balance' not in users_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN real_cash_balance REAL DEFAULT 0.0")
            print("✅ Added real_cash_balance column to users table")
        except Exception as e:
            print(f"❌ Error adding real_cash_balance: {e}")
    else:
        print("ℹ️ real_cash_balance column already exists")
    
    # Check current orders table structure
    cursor.execute("PRAGMA table_info(orders)")
    orders_cols = [col[1] for col in cursor.fetchall()]
    print(f"\nCurrent orders table columns: {orders_cols}")
    
    # Add is_demo if it doesn't exist
    if 'is_demo' not in orders_cols:
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN is_demo INTEGER DEFAULT 1")
            print("✅ Added is_demo column to orders table")
        except Exception as e:
            print(f"❌ Error adding is_demo: {e}")
    else:
        print("ℹ️ is_demo column already exists")
    
    conn.commit()
    print("\n✅ Migration completed successfully!")
    
    # Verify changes
    cursor.execute("PRAGMA table_info(users)")
    users_cols_after = [col[1] for col in cursor.fetchall()]
    print(f"\nUpdated users table columns: {users_cols_after}")
    
    cursor.execute("PRAGMA table_info(orders)")
    orders_cols_after = [col[1] for col in cursor.fetchall()]
    print(f"Updated orders table columns: {orders_cols_after}")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    conn.rollback()
    raise
finally:
    conn.close()

