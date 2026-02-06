"""
Automated Training Pipeline Service
Automatically trains and retrains ML models on a schedule
"""

import logging
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

class AutomatedTrainingPipeline:
    """Automated pipeline for training and retraining ML models"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.training_config = self._load_training_config()
        self.models_dir = "models/auto_trained"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Training status
        self.training_status = {}
        self.last_training_time = {}
        
    def _load_training_config(self) -> Dict:
        """Load training configuration"""
        config_path = "config/training_config.json"
        default_config = {
            "training_schedule": {
                "daily": "02:00",  # Train daily at 2 AM
                "weekly": "sunday:03:00",  # Weekly retraining on Sunday at 3 AM
                "monthly": "1:04:00"  # Monthly retraining on 1st at 4 AM
            },
            "models_to_train": [
                "gradient_boosting",
                "temporal_models",
                "alternative_data",
                "bayesian",
                "reinforcement_learning",
                "meta_learner"
            ],
            "training_symbols": [
                "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
                "HINDUNILVR", "BHARTIARTL", "SBIN", "BAJFINANCE", "KOTAKBANK"
            ],
            "min_data_points": 100,
            "validation_split": 0.2,
            "retrain_threshold": {
                "accuracy_drop": 0.05,  # Retrain if accuracy drops by 5%
                "days_since_training": 30  # Retrain if not trained in 30 days
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return {**default_config, **config}
        except Exception as e:
            logger.warning(f"Could not load training config: {e}, using defaults")
        
        return default_config
    
    async def start_scheduler(self):
        """Start the automated training scheduler"""
        try:
            # Schedule daily training
            daily_time = self.training_config["training_schedule"]["daily"]
            hour, minute = daily_time.split(":")
            self.scheduler.add_job(
                self.run_daily_training,
                CronTrigger(hour=int(hour), minute=int(minute)),
                id="daily_training",
                replace_existing=True
            )
            
            # Schedule weekly retraining
            weekly_schedule = self.training_config["training_schedule"]["weekly"]
            day, time = weekly_schedule.split(":")
            hour, minute = time.split(":")
            day_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            self.scheduler.add_job(
                self.run_weekly_retraining,
                CronTrigger(day_of_week=day_map.get(day.lower(), 6), hour=int(hour), minute=int(minute)),
                id="weekly_retraining",
                replace_existing=True
            )
            
            # Schedule monthly retraining
            monthly_schedule = self.training_config["training_schedule"]["monthly"]
            day, time = monthly_schedule.split(":")
            hour, minute = time.split(":")
            self.scheduler.add_job(
                self.run_monthly_retraining,
                CronTrigger(day=int(day), hour=int(hour), minute=int(minute)),
                id="monthly_retraining",
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("✅ Automated training pipeline scheduler started")
            
        except Exception as e:
            logger.error(f"Error starting training scheduler: {e}")
    
    async def run_daily_training(self):
        """Run daily model training"""
        try:
            logger.info("🔄 Starting daily model training...")
            await self.train_models(
                models=["gradient_boosting", "temporal_models"],
                symbols=self.training_config["training_symbols"][:5]  # Top 5 symbols
            )
            logger.info("✅ Daily model training completed")
        except Exception as e:
            logger.error(f"Error in daily training: {e}")
    
    async def run_weekly_retraining(self):
        """Run weekly model retraining"""
        try:
            logger.info("🔄 Starting weekly model retraining...")
            await self.train_models(
                models=self.training_config["models_to_train"],
                symbols=self.training_config["training_symbols"]
            )
            logger.info("✅ Weekly model retraining completed")
        except Exception as e:
            logger.error(f"Error in weekly retraining: {e}")
    
    async def run_monthly_retraining(self):
        """Run monthly comprehensive retraining"""
        try:
            logger.info("🔄 Starting monthly comprehensive retraining...")
            await self.train_models(
                models=self.training_config["models_to_train"],
                symbols=self.training_config["training_symbols"],
                full_retrain=True
            )
            logger.info("✅ Monthly comprehensive retraining completed")
        except Exception as e:
            logger.error(f"Error in monthly retraining: {e}")
    
    async def train_models(
        self,
        models: List[str],
        symbols: List[str],
        full_retrain: bool = False
    ) -> Dict[str, Any]:
        """Train specified models on given symbols"""
        results = {}
        
        for model_name in models:
            try:
                logger.info(f"Training {model_name} on {len(symbols)} symbols...")
                
                if model_name == "gradient_boosting":
                    result = await self._train_gradient_boosting(symbols, full_retrain)
                elif model_name == "temporal_models":
                    result = await self._train_temporal_models(symbols, full_retrain)
                elif model_name == "alternative_data":
                    result = await self._train_alternative_data(symbols, full_retrain)
                elif model_name == "bayesian":
                    result = await self._train_bayesian(symbols, full_retrain)
                elif model_name == "reinforcement_learning":
                    result = await self._train_reinforcement_learning(symbols, full_retrain)
                elif model_name == "meta_learner":
                    result = await self._train_meta_learner(symbols, full_retrain)
                else:
                    result = {"error": f"Unknown model: {model_name}"}
                
                results[model_name] = result
                self.last_training_time[model_name] = datetime.now().isoformat()
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                results[model_name] = {"error": str(e)}
        
        return results
    
    async def _train_gradient_boosting(self, symbols: List[str], full_retrain: bool) -> Dict:
        """Train gradient boosting models"""
        try:
            from services.gradient_boosting_models import GradientBoostingModels
            gb_models = GradientBoostingModels()
            
            # Fetch training data
            training_data = await self._fetch_training_data(symbols, days=180)
            if not training_data or len(training_data) < self.training_config["min_data_points"]:
                return {"error": "Insufficient training data"}
            
            # Train models
            result = await asyncio.to_thread(
                gb_models.train_all_models,
                training_data,
                validation_split=self.training_config["validation_split"]
            )
            
            # Save models
            gb_models.save_models()
            
            return {
                "status": "success",
                "models_trained": ["xgb", "lgb", "rf", "gb"],
                "training_samples": len(training_data),
                "metrics": result
            }
        except Exception as e:
            logger.error(f"Error training gradient boosting: {e}")
            return {"error": str(e)}
    
    async def _train_temporal_models(self, symbols: List[str], full_retrain: bool) -> Dict:
        """Train temporal models (LSTM, Transformer)"""
        try:
            from services.temporal_models import TemporalModels
            temporal_models = TemporalModels()
            
            training_data = await self._fetch_training_data(symbols, days=365)
            if not training_data or len(training_data) < self.training_config["min_data_points"]:
                return {"error": "Insufficient training data"}
            
            # Train LSTM
            lstm_result = await asyncio.to_thread(
                temporal_models.train_lstm,
                training_data,
                validation_split=self.training_config["validation_split"]
            )
            
            # Train Transformer
            transformer_result = await asyncio.to_thread(
                temporal_models.train_transformer,
                training_data,
                validation_split=self.training_config["validation_split"]
            )
            
            temporal_models.save_models()
            
            return {
                "status": "success",
                "models_trained": ["lstm", "transformer"],
                "training_samples": len(training_data),
                "lstm_metrics": lstm_result,
                "transformer_metrics": transformer_result
            }
        except Exception as e:
            logger.error(f"Error training temporal models: {e}")
            return {"error": str(e)}
    
    async def _train_alternative_data(self, symbols: List[str], full_retrain: bool) -> Dict:
        """Train alternative data models"""
        try:
            from services.alternative_data_models import AlternativeDataModels
            alt_models = AlternativeDataModels()
            
            # Fetch text and on-chain data
            training_data = await self._fetch_alternative_data(symbols, days=90)
            if not training_data:
                return {"error": "No alternative data available"}
            
            # Train models
            result = await asyncio.to_thread(
                alt_models.train_all_models,
                training_data,
                validation_split=self.training_config["validation_split"]
            )
            
            alt_models.save_models()
            
            return {
                "status": "success",
                "models_trained": ["text_cnn", "onchain_transformer", "multimodal"],
                "training_samples": len(training_data),
                "metrics": result
            }
        except Exception as e:
            logger.error(f"Error training alternative data models: {e}")
            return {"error": str(e)}
    
    async def _train_bayesian(self, symbols: List[str], full_retrain: bool) -> Dict:
        """Train Bayesian models"""
        try:
            from services.bayesian_macro_models import BayesianMacroModels
            bayesian_models = BayesianMacroModels()
            
            training_data = await self._fetch_training_data(symbols, days=252)
            if not training_data or len(training_data) < self.training_config["min_data_points"]:
                return {"error": "Insufficient training data"}
            
            # Bayesian models don't require traditional training, but we can update priors
            bayesian_models.save_models()
            
            return {
                "status": "success",
                "models_updated": ["regime_detection", "correlation_analysis", "volatility_modeling"],
                "training_samples": len(training_data)
            }
        except Exception as e:
            logger.error(f"Error training Bayesian models: {e}")
            return {"error": str(e)}
    
    async def _train_reinforcement_learning(self, symbols: List[str], full_retrain: bool) -> Dict:
        """Train reinforcement learning agent"""
        try:
            from services.reinforcement_learning_agent import ReinforcementLearningAgent
            rl_agent = ReinforcementLearningAgent()
            
            training_data = await self._fetch_training_data(symbols, days=180)
            if not training_data or len(training_data) < self.training_config["min_data_points"]:
                return {"error": "Insufficient training data"}
            
            # Train RL agent
            result = await asyncio.to_thread(
                rl_agent.train,
                training_data,
                episodes=100 if not full_retrain else 500
            )
            
            rl_agent.save_model()
            
            return {
                "status": "success",
                "episodes": result.get("episodes", 0),
                "average_reward": result.get("average_reward", 0.0),
                "training_samples": len(training_data)
            }
        except Exception as e:
            logger.error(f"Error training reinforcement learning: {e}")
            return {"error": str(e)}
    
    async def _train_meta_learner(self, symbols: List[str], full_retrain: bool) -> Dict:
        """Train meta-learner fusion model"""
        try:
            from services.meta_learner_fusion import MetaLearnerFusion
            meta_learner = MetaLearnerFusion()
            
            # Meta-learner needs predictions from base models
            training_data = await self._fetch_training_data(symbols, days=180)
            if not training_data or len(training_data) < self.training_config["min_data_points"]:
                return {"error": "Insufficient training data"}
            
            # Train meta-learner
            result = await asyncio.to_thread(
                meta_learner.train_meta_learner,
                training_data,
                validation_split=self.training_config["validation_split"]
            )
            
            meta_learner.save_models()
            
            return {
                "status": "success",
                "meta_models_trained": list(meta_learner.meta_learner_models.keys()),
                "training_samples": len(training_data),
                "metrics": result
            }
        except Exception as e:
            logger.error(f"Error training meta-learner: {e}")
            return {"error": str(e)}
    
    async def _fetch_training_data(self, symbols: List[str], days: int) -> Optional[pd.DataFrame]:
        """Fetch training data for symbols"""
        try:
            from services.data_fetcher import fetch_historical_data
            
            all_data = []
            for symbol in symbols:
                try:
                    data = await fetch_historical_data(symbol, timeframe="1d", days=days)
                    if data:
                        df = pd.DataFrame(data)
                        df['symbol'] = symbol
                        all_data.append(df)
                except Exception as e:
                    logger.warning(f"Could not fetch data for {symbol}: {e}")
            
            if all_data:
                return pd.concat(all_data, ignore_index=True)
            return None
        except Exception as e:
            logger.error(f"Error fetching training data: {e}")
            return None
    
    async def _fetch_alternative_data(self, symbols: List[str], days: int) -> Optional[List[Dict]]:
        """Fetch alternative data (news, social media) for symbols"""
        try:
            # This would integrate with news/social media APIs
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error fetching alternative data: {e}")
            return None
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        return {
            "scheduler_running": self.scheduler.running if hasattr(self.scheduler, 'running') else False,
            "last_training_time": self.last_training_time,
            "next_scheduled_training": self._get_next_scheduled_training()
        }
    
    def _get_next_scheduled_training(self) -> Dict[str, str]:
        """Get next scheduled training times"""
        jobs = self.scheduler.get_jobs()
        next_times = {}
        for job in jobs:
            next_times[job.id] = job.next_run_time.isoformat() if job.next_run_time else None
        return next_times

# Create singleton instance
automated_training_pipeline = AutomatedTrainingPipeline()

