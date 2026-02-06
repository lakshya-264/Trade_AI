#!/usr/bin/env python3
"""
Fix AI Analysis Table - Add Missing Columns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.database import DATABASE_URL

def fix_ai_analysis_table():
    """Add missing columns to ai_analysis table"""
    print("🔧 Fixing AI Analysis table...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check what columns exist
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ai_analysis'
                ORDER BY ordinal_position
            """))
            
            existing_columns = {row[0]: row[1] for row in result.fetchall()}
            print(f"📋 Existing columns: {list(existing_columns.keys())}")
            
            # Add missing columns
            missing_columns = [
                ("reasoning", "TEXT"),
                ("technical_indicators", "JSONB"),
                ("sentiment_data", "JSONB"),
                ("fundamental_metrics", "JSONB"),
                ("price_target", "FLOAT"),
                ("stop_loss", "FLOAT"),
                ("risk_level", "VARCHAR(20)"),
                ("expires_at", "TIMESTAMP")
            ]
            
            for column_name, column_type in missing_columns:
                if column_name not in existing_columns:
                    print(f"➕ Adding column: {column_name} ({column_type})")
                    conn.execute(text(f"""
                        ALTER TABLE ai_analysis 
                        ADD COLUMN {column_name} {column_type}
                    """))
                else:
                    print(f"✅ Column already exists: {column_name}")
            
            conn.commit()
            print("✅ AI Analysis table fixed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing AI Analysis table: {str(e)}")
        return False

def verify_ai_analysis_table():
    """Verify AI Analysis table structure"""
    print("🔍 Verifying AI Analysis table...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ai_analysis'
                ORDER BY ordinal_position
            """))
            
            columns = {row[0]: row[1] for row in result.fetchall()}
            
            required_columns = [
                "id", "symbol", "analysis_type", "signal", "confidence",
                "reasoning", "technical_indicators", "sentiment_data", 
                "fundamental_metrics", "price_target", "stop_loss", 
                "risk_level", "created_at", "expires_at"
            ]
            
            missing = [col for col in required_columns if col not in columns]
            
            if missing:
                print(f"❌ Missing columns: {missing}")
                return False
            else:
                print("✅ All required columns present")
                print(f"📋 Columns: {list(columns.keys())}")
                return True
                
    except Exception as e:
        print(f"❌ Error verifying table: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Fix AI Analysis Table")
    print("=" * 30)
    
    if fix_ai_analysis_table():
        if verify_ai_analysis_table():
            print("\n🎉 AI Analysis table migration completed successfully!")
            print("You can now test AI analysis functionality.")
        else:
            print("\n⚠️ Migration completed but verification failed")
    else:
        print("\n❌ Migration failed!")

if __name__ == "__main__":
    main()
