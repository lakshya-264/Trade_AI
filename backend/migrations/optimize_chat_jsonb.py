"""
Database migration to optimize chat messages metadata for JSONB performance
"""

import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_database_url

async def optimize_chat_jsonb():
    """Optimize chat messages table for JSONB performance"""
    
    # Get database URL
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()
            
            try:
                print("Starting JSONB optimization...")
                
                # Check if metadata_json column exists and is already JSONB
                result = connection.execute(text("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'chat_messages' 
                    AND column_name = 'metadata_json'
                """))
                
                column_type = result.fetchone()
                if not column_type:
                    print("❌ chat_messages table or metadata_json column not found")
                    return False
                
                if column_type[0] == 'jsonb':
                    print("✅ metadata_json is already JSONB type")
                else:
                    print("🔄 Converting metadata_json to JSONB...")
                    # Convert to JSONB
                    connection.execute(text("""
                        ALTER TABLE chat_messages 
                        ALTER COLUMN metadata_json TYPE jsonb USING metadata_json::jsonb
                    """))
                    print("✅ Successfully converted to JSONB")
                
                # Create GIN index for fast JSON queries
                print("🔄 Creating GIN index for metadata_json...")
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_chat_messages_metadata_json_gin 
                    ON chat_messages USING GIN (metadata_json)
                """))
                print("✅ GIN index created successfully")
                
                # Create other useful indexes
                print("🔄 Creating additional indexes...")
                
                # Index for symbol queries
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_prediction_history_symbol 
                    ON prediction_history(symbol)
                """))
                
                # Index for user sessions
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id 
                    ON chat_sessions(user_id)
                """))
                
                # Index for message types
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_chat_messages_type 
                    ON chat_messages(message_type)
                """))
                
                # Index for AI generated messages
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_chat_messages_ai_generated 
                    ON chat_messages(is_ai_generated)
                """))
                
                print("✅ Additional indexes created successfully")
                
                # Commit transaction
                trans.commit()
                print("✅ JSONB optimization completed successfully!")
                
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Error during optimization: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    finally:
        engine.dispose()

async def verify_optimization():
    """Verify that the optimization was successful"""
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as connection:
            # Check JSONB type
            result = connection.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'chat_messages' 
                AND column_name = 'metadata_json'
            """))
            
            column_type = result.fetchone()
            if column_type and column_type[0] == 'jsonb':
                print("✅ Verification: metadata_json is JSONB")
            else:
                print("❌ Verification failed: metadata_json is not JSONB")
                return False
            
            # Check indexes
            result = connection.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'chat_messages' 
                AND indexname LIKE '%metadata_json%'
            """))
            
            indexes = result.fetchall()
            if indexes:
                print(f"✅ Verification: Found {len(indexes)} metadata_json indexes")
                for idx in indexes:
                    print(f"   - {idx[0]}")
            else:
                print("❌ Verification failed: No metadata_json indexes found")
                return False
            
            print("✅ All optimizations verified successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    async def main():
        print("🚀 Starting database JSONB optimization...")
        
        success = await optimize_chat_jsonb()
        
        if success:
            print("\n🔍 Verifying optimization...")
            verify_success = await verify_optimization()
            
            if verify_success:
                print("\n🎉 Database optimization completed successfully!")
                print("\nBenefits:")
                print("• Faster JSON queries on chat metadata")
                print("• Better performance for signal analysis")
                print("• Optimized indexes for common queries")
            else:
                print("\n⚠️  Optimization completed but verification failed")
        else:
            print("\n❌ Database optimization failed")
    
    asyncio.run(main())
