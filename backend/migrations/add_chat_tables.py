"""
Database migration to add AI chatbot tables
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

def upgrade():
    """Add chat tables to database"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trader:secret@172.31.37.244:5432/trader_ai")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with engine.connect() as conn:
        # Create chat_sessions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                session_id VARCHAR UNIQUE NOT NULL,
                session_name VARCHAR DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                message_count INTEGER DEFAULT 0
            )
        """))
        
        # Create chat_messages table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR NOT NULL REFERENCES chat_sessions(session_id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                message_type VARCHAR NOT NULL,
                content TEXT NOT NULL,
                metadata_json JSON,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_ai_generated BOOLEAN DEFAULT FALSE,
                confidence_score FLOAT DEFAULT 0.0
            )
        """))
        
        # Create prediction_history table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prediction_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                symbol VARCHAR NOT NULL,
                prediction_type VARCHAR NOT NULL,
                prediction_data JSON NOT NULL,
                confidence_score FLOAT,
                actual_result JSON,
                accuracy_score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """))
        
        # Create market_news table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS market_news (
                id SERIAL PRIMARY KEY,
                title VARCHAR NOT NULL,
                content TEXT,
                source VARCHAR,
                url VARCHAR,
                sentiment_score FLOAT,
                sentiment_label VARCHAR,
                symbols_mentioned JSON,
                published_at TIMESTAMP,
                embedding TEXT,
                category VARCHAR,
                importance_score FLOAT DEFAULT 0.0
            )
        """))
        
        # Create trading_knowledge table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trading_knowledge (
                id SERIAL PRIMARY KEY,
                category VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                content TEXT NOT NULL,
                tags JSON,
                embedding TEXT,
                difficulty_level VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """))
        
        # Create chat_context table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_context (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR NOT NULL REFERENCES chat_sessions(session_id),
                context_type VARCHAR NOT NULL,
                context_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create indexes for better performance
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prediction_history_user_id ON prediction_history(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prediction_history_symbol ON prediction_history(symbol)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_market_news_published_at ON market_news(published_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_market_news_sentiment_score ON market_news(sentiment_score)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trading_knowledge_category ON trading_knowledge(category)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_context_session_id ON chat_context(session_id)"))
        
        conn.commit()
        print("✅ Chat tables created successfully!")

def downgrade():
    """Remove chat tables from database"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trader:secret@172.31.37.244:5432/trader_ai")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Drop tables in reverse order
        conn.execute(text("DROP TABLE IF EXISTS chat_context"))
        conn.execute(text("DROP TABLE IF EXISTS trading_knowledge"))
        conn.execute(text("DROP TABLE IF EXISTS market_news"))
        conn.execute(text("DROP TABLE IF EXISTS prediction_history"))
        conn.execute(text("DROP TABLE IF EXISTS chat_messages"))
        conn.execute(text("DROP TABLE IF EXISTS chat_sessions"))
        
        conn.commit()
        print("✅ Chat tables removed successfully!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()

