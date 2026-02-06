"""
Migration: Create prediction tracking tables
"""

from sqlalchemy import text
from core.database_unified import engine

def create_prediction_tracking_tables():
    """Create tables for prediction tracking"""
    
    with engine.connect() as conn:
        # Create price_prediction_records table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS price_prediction_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(50) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                prediction_date DATETIME NOT NULL,
                target_date DATE NOT NULL,
                predicted_price FLOAT NOT NULL,
                current_price FLOAT NOT NULL,
                predicted_change_percent FLOAT NOT NULL,
                confidence FLOAT NOT NULL,
                price_range_low_68 FLOAT,
                price_range_high_68 FLOAT,
                price_range_low_95 FLOAT,
                price_range_high_95 FLOAT,
                model_type VARCHAR(50) NOT NULL,
                model_contributions TEXT,
                actual_price FLOAT,
                actual_change_percent FLOAT,
                evaluated BOOLEAN DEFAULT 0,
                evaluated_at DATETIME,
                price_error FLOAT,
                price_error_percent FLOAT,
                direction_correct BOOLEAN,
                within_range_68 BOOLEAN,
                within_range_95 BOOLEAN,
                analysis_data_hash VARCHAR(64),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_date ON price_prediction_records(symbol, timeframe, prediction_date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_evaluated_timeframe ON price_prediction_records(evaluated, timeframe, target_date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_symbol ON price_prediction_records(symbol)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_timeframe ON price_prediction_records(timeframe)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prediction_date ON price_prediction_records(prediction_date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_evaluated ON price_prediction_records(evaluated)"))
        
        # Create model_performance_metrics table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS model_performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_type VARCHAR(50) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                evaluation_period_start DATE NOT NULL,
                evaluation_period_end DATE NOT NULL,
                total_predictions INTEGER DEFAULT 0,
                evaluated_predictions INTEGER DEFAULT 0,
                mean_absolute_error FLOAT,
                mean_absolute_percentage_error FLOAT,
                root_mean_squared_error FLOAT,
                direction_accuracy FLOAT,
                range_68_accuracy FLOAT,
                range_95_accuracy FLOAT,
                avg_confidence FLOAT,
                high_confidence_accuracy FLOAT,
                error_percentiles TEXT,
                last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(model_type, timeframe, evaluation_period_start)
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_model_timeframe_period ON model_performance_metrics(model_type, timeframe, evaluation_period_start)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_model_type ON model_performance_metrics(model_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_timeframe_perf ON model_performance_metrics(timeframe)"))
        
        # Create model_training_logs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS model_training_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_type VARCHAR(50) NOT NULL,
                model_category VARCHAR(50) NOT NULL,
                timeframe VARCHAR(10),
                training_started_at DATETIME NOT NULL,
                training_completed_at DATETIME,
                status VARCHAR(20) NOT NULL,
                symbols_used TEXT,
                data_points_count INTEGER,
                training_period_start DATE,
                training_period_end DATE,
                train_loss FLOAT,
                validation_loss FLOAT,
                test_loss FLOAT,
                training_metrics TEXT,
                model_file_path VARCHAR(500),
                model_version VARCHAR(50),
                model_size_mb FLOAT,
                error_message TEXT,
                error_traceback TEXT,
                training_config TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_model_status_date ON model_training_logs(model_type, status, training_started_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_model_type_log ON model_training_logs(model_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_status ON model_training_logs(status)"))
        
        # Create model_retraining_schedules table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS model_retraining_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_type VARCHAR(50) NOT NULL,
                model_category VARCHAR(50) NOT NULL,
                timeframe VARCHAR(10),
                schedule_type VARCHAR(20) NOT NULL,
                schedule_config TEXT,
                retrain_on_accuracy_drop BOOLEAN DEFAULT 0,
                accuracy_drop_threshold FLOAT,
                min_days_between_retraining INTEGER DEFAULT 7,
                enabled BOOLEAN DEFAULT 1,
                last_retrained_at DATETIME,
                next_retraining_at DATETIME,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(model_type, timeframe)
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_model_schedule_unique ON model_retraining_schedules(model_type, timeframe)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_enabled ON model_retraining_schedules(enabled)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_next_retraining ON model_retraining_schedules(next_retraining_at)"))
        
        conn.commit()
        print("✅ Prediction tracking tables created successfully")

if __name__ == "__main__":
    create_prediction_tracking_tables()
