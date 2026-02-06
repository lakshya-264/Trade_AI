"""
Advanced Learning Coordinator
Coordinates all advanced learning services for unified operation
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from services.automatic_model_retraining import automatic_model_retraining
from services.dynamic_feature_selection import dynamic_feature_selection
from services.adaptive_algorithm_selection import adaptive_algorithm_selection
from services.realtime_parameter_tuning import realtime_parameter_tuning

logger = logging.getLogger(__name__)

class AdvancedLearningCoordinator:
    """Coordinates all advanced learning services"""
    
    def __init__(self):
        self.services = {
            'retraining': automatic_model_retraining,
            'feature_selection': dynamic_feature_selection,
            'algorithm_selection': adaptive_algorithm_selection,
            'parameter_tuning': realtime_parameter_tuning
        }
    
    def process_learning_cycle(
        self,
        symbol: str,
        model_name: str,
        performance_metrics: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a complete learning cycle for a model/symbol
        
        Args:
            symbol: Stock symbol
            model_name: Name of the model
            performance_metrics: Current performance metrics
            context: Additional context (optional)
        
        Returns:
            Dict with all learning results
        """
        try:
            results = {
                "symbol": symbol,
                "model_name": model_name,
                "timestamp": datetime.now().isoformat(),
                "services": {}
            }
            
            # 1. Check and retrain model if needed
            retraining_status = automatic_model_retraining.get_retraining_status(model_name)
            results["services"]["retraining"] = {
                "status": retraining_status,
                "needs_retraining": retraining_status.get("needs_retraining", False)
            }
            
            # 2. Get algorithm selection
            algorithm_result = adaptive_algorithm_selection.select_best_algorithm(symbol)
            results["services"]["algorithm_selection"] = algorithm_result
            
            # 3. Get current parameters
            current_params = realtime_parameter_tuning.get_current_parameters(model_name)
            results["services"]["parameter_tuning"] = {
                "current_parameters": current_params,
                "should_optimize": realtime_parameter_tuning._should_tune(model_name)
            }
            
            # 4. Get feature selection status
            selected_features = dynamic_feature_selection.get_selected_features(model_name)
            results["services"]["feature_selection"] = {
                "selected_features": selected_features,
                "n_features": len(selected_features)
            }
            
            # 5. Overall learning status
            results["overall_status"] = self._calculate_overall_status(results["services"])
            
            logger.info(f"Learning cycle processed for {symbol}/{model_name}")
            
            return {
                "success": True,
                "data": results
            }
            
        except Exception as e:
            logger.error(f"Error in learning cycle: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_overall_status(self, services_results: Dict) -> Dict[str, Any]:
        """Calculate overall learning status"""
        statuses = []
        
        # Check each service
        if services_results.get("retraining", {}).get("needs_retraining"):
            statuses.append("Model needs retraining")
        
        if services_results.get("algorithm_selection", {}).get("algorithm_changed"):
            statuses.append("Algorithm changed")
        
        if services_results.get("parameter_tuning", {}).get("should_optimize"):
            statuses.append("Parameters need optimization")
        
        if not services_results.get("feature_selection", {}).get("selected_features"):
            statuses.append("Feature selection needed")
        
        return {
            "active_learning": len(statuses) > 0,
            "statuses": statuses,
            "all_optimal": len(statuses) == 0
        }
    
    def get_comprehensive_status(
        self,
        symbol: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive status of all learning services"""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "services": {}
            }
            
            # Retraining status
            if model_name:
                retraining_status = automatic_model_retraining.get_retraining_status(model_name)
                status["services"]["retraining"] = retraining_status
            
            # Algorithm selection status
            if symbol:
                algorithm_recs = adaptive_algorithm_selection.get_algorithm_recommendations(symbol)
                status["services"]["algorithm_selection"] = algorithm_recs
            
            # Parameter tuning status
            if model_name:
                params = realtime_parameter_tuning.get_current_parameters(model_name)
                history = realtime_parameter_tuning.get_parameter_history(model_name, days=7)
                status["services"]["parameter_tuning"] = {
                    "current_parameters": params,
                    "recent_history": history
                }
            
            # Feature selection status
            if model_name:
                features = dynamic_feature_selection.get_selected_features(model_name)
                importance = dynamic_feature_selection.get_feature_importance(model_name)
                status["services"]["feature_selection"] = {
                    "selected_features": features,
                    "feature_importance": importance
                }
            
            return {
                "success": True,
                "data": status
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive status: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global instance
advanced_learning_coordinator = AdvancedLearningCoordinator()

