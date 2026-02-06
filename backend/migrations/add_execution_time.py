#!/usr/bin/env python3
"""
Add execution_time field to orders table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.database import DATABASE_URL

def add_execution_time_column():
    """Add execution_time column to orders table"""
    print("🔧 Adding execution_time column to orders table...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'orders' AND column_name = 'execution_time'
            """))
            
            if result.fetchone():
                print("✅ execution_time column already exists")
                return True
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE orders 
                ADD COLUMN execution_time TIMESTAMP
            """))
            
            conn.commit()
            print("✅ execution_time column added successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error adding execution_time column: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Adding execution_time to orders table")
    print("=" * 40)
    
    if add_execution_time_column():
        print("🎉 Migration completed successfully!")
    else:
        print("❌ Migration failed!")

if __name__ == "__main__":
    main()
