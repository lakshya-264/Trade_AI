"""
Dynamic Feature Selection Service
Automatically selects best features and adjusts feature importance
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sklearn.feature_selection import (
    SelectKBest, f_regression, f_classif,
    mutual_info_regression, mutual_info_classif,
    RFE, RFECV
)
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import accuracy_score, mean_squared_error

logger = logging.getLogger(__name__)

class DynamicFeatureSelection:
    """Dynamically select best features based on performance"""
    
    def __init__(self):
        self.feature_importance_history = {}
        self.selected_features = {}
        self.feature_scores = {}
        
        # Selection methods
        self.selection_methods = {
            'univariate': self._univariate_selection,
            'mutual_info': self._mutual_info_selection,
            'rfe': self._rfe_selection,
            'importance': self._importance_based_selection
        }
    
    def select_features(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_name: str,
        method: str = 'auto',
        n_features: Optional[int] = None,
        task_type: str = 'regression'  # 'regression' or 'classification'
    ) -> Dict[str, Any]:
        """
        Select best features for a model
        
        Args:
            X: Feature matrix
            y: Target variable
            model_name: Name of the model
            method: Selection method ('auto', 'univariate', 'mutual_info', 'rfe', 'importance')
            n_features: Number of features to select (auto if None)
            task_type: 'regression' or 'classification'
        
        Returns:
            Dict with selected features and scores
        """
        try:
            if method == 'auto':
                method = self._choose_best_method(X, y, task_type)
            
            if method not in self.selection_methods:
                method = 'importance'  # Default fallback
            
            # Determine number of features
            if n_features is None:
                n_features = min(20, len(X.columns) // 2)  # Select top 50% or max 20
            
            # Select features
            selection_result = self.selection_methods[method](
                X, y, n_features, task_type
            )
            
            # Update feature importance history
            self._update_feature_history(model_name, selection_result)
            
            # Store selected features
            self.selected_features[model_name] = selection_result['selected_features']
            self.feature_scores[model_name] = selection_result['feature_scores']
            
            logger.info(f"Selected {len(selection_result['selected_features'])} features for {model_name} using {method}")
            
            return {
                "success": True,
                "method": method,
                "selected_features": selection_result['selected_features'],
                "feature_scores": selection_result['feature_scores'],
                "n_features": len(selection_result['selected_features']),
                "total_features": len(X.columns),
                "reduction": f"{(1 - len(selection_result['selected_features']) / len(X.columns)) * 100:.1f}%"
            }
            
        except Exception as e:
            logger.error(f"Error in feature selection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _univariate_selection(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_features: int,
        task_type: str
    ) -> Dict[str, Any]:
        """Univariate feature selection"""
        if task_type == 'regression':
            selector = SelectKBest(score_func=f_regression, k=n_features)
        else:
            selector = SelectKBest(score_func=f_classif, k=n_features)
        
        selector.fit(X, y)
        
        selected_indices = selector.get_support(indices=True)
        selected_features = X.columns[selected_indices].tolist()
        feature_scores = dict(zip(X.columns, selector.scores_))
        
        return {
            "selected_features": selected_features,
            "feature_scores": feature_scores
        }
    
    def _mutual_info_selection(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_features: int,
        task_type: str
    ) -> Dict[str, Any]:
        """Mutual information based selection"""
        if task_type == 'regression':
            scores = mutual_info_regression(X, y, random_state=42)
        else:
            scores = mutual_info_classif(X, y, random_state=42)
        
        # Get top n_features
        top_indices = np.argsort(scores)[-n_features:][::-1]
        selected_features = X.columns[top_indices].tolist()
        feature_scores = dict(zip(X.columns, scores))
        
        return {
            "selected_features": selected_features,
            "feature_scores": feature_scores
        }
    
    def _rfe_selection(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_features: int,
        task_type: str
    ) -> Dict[str, Any]:
        """Recursive Feature Elimination"""
        if task_type == 'regression':
            estimator = RandomForestRegressor(n_estimators=50, random_state=42)
        else:
            estimator = RandomForestClassifier(n_estimators=50, random_state=42)
        
        selector = RFE(estimator=estimator, n_features_to_select=n_features)
        selector.fit(X, y)
        
        selected_indices = selector.get_support(indices=True)
        selected_features = X.columns[selected_indices].tolist()
        
        # Get feature importance from the estimator
        feature_importance = selector.estimator_.feature_importances_
        feature_scores = dict(zip(X.columns, feature_importance))
        
        return {
            "selected_features": selected_features,
            "feature_scores": feature_scores
        }
    
    def _importance_based_selection(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_features: int,
        task_type: str
    ) -> Dict[str, Any]:
        """Feature importance based selection using Random Forest"""
        if task_type == 'regression':
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        model.fit(X, y)
        
        # Get feature importance
        importance = model.feature_importances_
        
        # Get top n_features
        top_indices = np.argsort(importance)[-n_features:][::-1]
        selected_features = X.columns[top_indices].tolist()
        feature_scores = dict(zip(X.columns, importance))
        
        return {
            "selected_features": selected_features,
            "feature_scores": feature_scores
        }
    
    def _choose_best_method(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        task_type: str
    ) -> str:
        """Choose best selection method based on data characteristics"""
        # Simple heuristic: use importance for small datasets, RFE for larger
        if len(X) < 1000:
            return 'importance'
        elif len(X.columns) < 50:
            return 'mutual_info'
        else:
            return 'rfe'
    
    def _update_feature_history(
        self,
        model_name: str,
        selection_result: Dict[str, Any]
    ):
        """Update feature importance history"""
        if model_name not in self.feature_importance_history:
            self.feature_importance_history[model_name] = []
        
        self.feature_importance_history[model_name].append({
            'features': selection_result['selected_features'],
            'scores': selection_result['feature_scores'],
            'timestamp': datetime.now()
        })
        
        # Keep only last 50 selections
        if len(self.feature_importance_history[model_name]) > 50:
            self.feature_importance_history[model_name] = self.feature_importance_history[model_name][-50:]
    
    def adjust_feature_importance(
        self,
        model_name: str,
        performance_feedback: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Adjust feature importance based on performance feedback
        
        Args:
            model_name: Name of the model
            performance_feedback: Dict mapping feature names to performance impact
        
        Returns:
            Updated feature importance
        """
        try:
            if model_name not in self.feature_scores:
                return {
                    "success": False,
                    "error": f"No feature scores found for {model_name}"
                }
            
            current_scores = self.feature_scores[model_name]
            
            # Adjust scores based on feedback
            # Positive feedback increases importance, negative decreases
            for feature, impact in performance_feedback.items():
                if feature in current_scores:
                    # Adjust by impact (normalized to 0-1 range)
                    adjustment = impact * 0.1  # 10% adjustment per unit impact
                    current_scores[feature] = max(0, current_scores[feature] + adjustment)
            
            # Renormalize scores
            total = sum(current_scores.values())
            if total > 0:
                current_scores = {k: v / total for k, v in current_scores.items()}
            
            self.feature_scores[model_name] = current_scores
            
            logger.info(f"Adjusted feature importance for {model_name}")
            
            return {
                "success": True,
                "updated_scores": current_scores,
                "message": "Feature importance adjusted based on performance feedback"
            }
            
        except Exception as e:
            logger.error(f"Error adjusting feature importance: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_selected_features(self, model_name: str) -> List[str]:
        """Get currently selected features for a model"""
        return self.selected_features.get(model_name, [])
    
    def get_feature_importance(self, model_name: str) -> Dict[str, float]:
        """Get feature importance scores for a model"""
        return self.feature_scores.get(model_name, {})

# Global instance
dynamic_feature_selection = DynamicFeatureSelection()

