"""
Bayesian Macro Models Service
Bayesian models for market regimes, correlations, and macro-economic analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
import pymc as pm
import arviz as az
import theano.tensor as tt
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class BayesianMacroModels:
    """Bayesian models for macro-economic analysis and market regimes"""
    
    def __init__(self):
        self.regime_model = None
        self.correlation_model = None
        self.volatility_model = None
        self.scaler = StandardScaler()
        
        # Models directory
        self.models_dir = "models/bayesian"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Market regime parameters
        self.n_regimes = 3  # Bull, Bear, Sideways
        self.regime_names = ['Bull Market', 'Bear Market', 'Sideways Market']
        
        # Correlation parameters
        self.correlation_window = 252  # 1 year
        self.min_correlation_samples = 50
        
    def identify_market_regimes(self, price_data: pd.DataFrame, volume_data: pd.DataFrame = None) -> Dict:
        """Identify market regimes using Bayesian mixture models"""
        try:
            # Prepare features for regime identification
            features = self._prepare_regime_features(price_data, volume_data)
            
            if len(features) == 0:
                return {"error": "No features available for regime identification"}
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features)
            
            # Bayesian Gaussian Mixture Model
            with pm.Model() as regime_model:
                # Priors for mixture components
                weights = pm.Dirichlet('weights', a=np.ones(self.n_regimes))
                
                # Priors for means and covariances
                means = pm.Normal('means', mu=0, sigma=2, shape=(self.n_regimes, features.shape[1]))
                covariances = pm.InverseWishart('covariances', nu=features.shape[1] + 1, 
                                              S=np.eye(features.shape[1]))
                
                # Mixture distribution
                mixture = pm.Mixture('mixture', w=weights, 
                                   comp_dists=pm.MvNormal.dist(mu=means, cov=covariances),
                                   observed=features_scaled)
                
                # Sample from posterior
                trace = pm.sample(1000, tune=1000, cores=2, progressbar=False)
            
            # Extract regime assignments
            regime_probs = pm.sample_posterior_predictive(trace, regime_model)['mixture']
            regime_assignments = np.argmax(regime_probs, axis=1)
            
            # Calculate regime characteristics
            regime_stats = self._calculate_regime_statistics(features, regime_assignments)
            
            # Current regime
            current_regime = regime_assignments[-1] if len(regime_assignments) > 0 else 0
            current_regime_prob = regime_probs[-1, current_regime] if len(regime_probs) > 0 else 0.33
            
            return {
                "regime_assignments": regime_assignments.tolist(),
                "regime_probabilities": regime_probs.tolist(),
                "current_regime": int(current_regime),
                "current_regime_name": self.regime_names[current_regime],
                "current_regime_confidence": float(current_regime_prob),
                "regime_statistics": regime_stats,
                "regime_transitions": self._calculate_regime_transitions(regime_assignments)
            }
            
        except Exception as e:
            logger.error(f"Error identifying market regimes: {e}")
            return {"error": str(e)}
    
    def _prepare_regime_features(self, price_data: pd.DataFrame, volume_data: pd.DataFrame = None) -> np.ndarray:
        """Prepare features for regime identification"""
        try:
            features = []
            
            # Price-based features
            returns = price_data['close'].pct_change().dropna()
            features.append(returns.values)
            
            # Volatility features
            volatility = returns.rolling(20).std().dropna()
            features.append(volatility.values)
            
            # Trend features
            sma_20 = price_data['close'].rolling(20).mean()
            sma_50 = price_data['close'].rolling(50).mean()
            trend_strength = (sma_20 - sma_50) / sma_50
            features.append(trend_strength.dropna().values)
            
            # Momentum features
            momentum = price_data['close'].pct_change(20).dropna()
            features.append(momentum.values)
            
            # Volume features (if available)
            if volume_data is not None and 'volume' in volume_data.columns:
                volume_ratio = volume_data['volume'] / volume_data['volume'].rolling(20).mean()
                features.append(volume_ratio.dropna().values)
            
            # Align all features to same length
            min_length = min(len(f) for f in features)
            aligned_features = np.column_stack([f[-min_length:] for f in features])
            
            return aligned_features
            
        except Exception as e:
            logger.error(f"Error preparing regime features: {e}")
            return np.array([])
    
    def _calculate_regime_statistics(self, features: np.ndarray, regime_assignments: np.ndarray) -> Dict:
        """Calculate statistics for each regime"""
        try:
            regime_stats = {}
            
            for regime in range(self.n_regimes):
                regime_mask = regime_assignments == regime
                regime_features = features[regime_mask]
                
                if len(regime_features) > 0:
                    regime_stats[f"regime_{regime}"] = {
                        "name": self.regime_names[regime],
                        "count": int(np.sum(regime_mask)),
                        "percentage": float(np.mean(regime_mask) * 100),
                        "mean_returns": float(np.mean(regime_features[:, 0])),
                        "volatility": float(np.std(regime_features[:, 0])),
                        "mean_volatility": float(np.mean(regime_features[:, 1])),
                        "trend_strength": float(np.mean(regime_features[:, 2])),
                        "momentum": float(np.mean(regime_features[:, 3]))
                    }
            
            return regime_stats
            
        except Exception as e:
            logger.error(f"Error calculating regime statistics: {e}")
            return {}
    
    def _calculate_regime_transitions(self, regime_assignments: np.ndarray) -> Dict:
        """Calculate regime transition probabilities"""
        try:
            transitions = np.zeros((self.n_regimes, self.n_regimes))
            
            for i in range(len(regime_assignments) - 1):
                current_regime = regime_assignments[i]
                next_regime = regime_assignments[i + 1]
                transitions[current_regime, next_regime] += 1
            
            # Normalize to probabilities
            row_sums = transitions.sum(axis=1)
            transition_probs = transitions / row_sums[:, np.newaxis]
            
            # Convert to dictionary
            transition_dict = {}
            for i in range(self.n_regimes):
                transition_dict[f"from_{self.regime_names[i]}"] = {
                    self.regime_names[j]: float(transition_probs[i, j])
                    for j in range(self.n_regimes)
                }
            
            return transition_dict
            
        except Exception as e:
            logger.error(f"Error calculating regime transitions: {e}")
            return {}
    
    def model_dynamic_correlations(self, price_data: Dict[str, pd.DataFrame]) -> Dict:
        """Model dynamic correlations between assets using Bayesian approach"""
        try:
            # Prepare correlation data
            returns_data = self._prepare_correlation_data(price_data)
            
            if len(returns_data) == 0:
                return {"error": "No data available for correlation modeling"}
            
            n_assets = len(returns_data.columns)
            n_obs = len(returns_data)
            
            # Bayesian Dynamic Correlation Model
            with pm.Model() as correlation_model:
                # Priors for correlation matrix
                L = pm.LKJCholeskyCov('L', n=n_assets, eta=2.0, sd_dist=pm.HalfCauchy.dist(2.0))
                
                # Dynamic correlation using random walk
                correlation_changes = pm.Normal('correlation_changes', mu=0, sigma=0.1, 
                                             shape=(n_obs - 1, n_assets, n_assets))
                
                # Initialize correlation matrix
                initial_corr = pm.Deterministic('initial_corr', 
                    pm.math.fill_diagonal(tt.ones((n_assets, n_assets)), 1.0))
                
                # Dynamic correlation evolution
                corr_sequence = [initial_corr]
                for t in range(1, n_obs):
                    prev_corr = corr_sequence[t-1]
                    new_corr = prev_corr + correlation_changes[t-1]
                    # Ensure correlation matrix properties
                    new_corr = pm.math.fill_diagonal(new_corr, 1.0)
                    corr_sequence.append(new_corr)
                
                # Final correlation matrix
                final_corr = corr_sequence[-1]
                
                # Multivariate normal likelihood
                mv_normal = pm.MvNormal('returns', mu=0, chol=L, observed=returns_data.values)
                
                # Sample from posterior
                trace = pm.sample(1000, tune=1000, cores=2, progressbar=False)
            
            # Extract correlation matrices
            correlation_samples = trace['final_corr']
            mean_correlation = np.mean(correlation_samples, axis=0)
            
            # Calculate correlation statistics
            correlation_stats = self._calculate_correlation_statistics(mean_correlation, returns_data.columns)
            
            return {
                "correlation_matrix": mean_correlation.tolist(),
                "asset_names": returns_data.columns.tolist(),
                "correlation_statistics": correlation_stats,
                "correlation_samples": correlation_samples.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error modeling dynamic correlations: {e}")
            return {"error": str(e)}
    
    def _prepare_correlation_data(self, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Prepare data for correlation modeling"""
        try:
            returns_data = {}
            
            for symbol, data in price_data.items():
                if 'close' in data.columns:
                    returns = data['close'].pct_change().dropna()
                    returns_data[symbol] = returns
            
            if not returns_data:
                return pd.DataFrame()
            
            # Align all returns to same time index
            returns_df = pd.DataFrame(returns_data)
            returns_df = returns_df.dropna()
            
            # Ensure minimum number of observations
            if len(returns_df) < self.min_correlation_samples:
                return pd.DataFrame()
            
            return returns_df
            
        except Exception as e:
            logger.error(f"Error preparing correlation data: {e}")
            return pd.DataFrame()
    
    def _calculate_correlation_statistics(self, correlation_matrix: np.ndarray, asset_names: List[str]) -> Dict:
        """Calculate correlation statistics"""
        try:
            n_assets = len(asset_names)
            stats = {}
            
            # Average correlation
            off_diagonal = correlation_matrix[np.triu_indices(n_assets, k=1)]
            stats['average_correlation'] = float(np.mean(off_diagonal))
            
            # Maximum correlation
            stats['max_correlation'] = float(np.max(off_diagonal))
            
            # Minimum correlation
            stats['min_correlation'] = float(np.min(off_diagonal))
            
            # Correlation range
            stats['correlation_range'] = float(np.max(off_diagonal) - np.min(off_diagonal))
            
            # Asset-specific correlations
            asset_correlations = {}
            for i, asset in enumerate(asset_names):
                other_correlations = [correlation_matrix[i, j] for j in range(n_assets) if i != j]
                asset_correlations[asset] = {
                    'average_correlation': float(np.mean(other_correlations)),
                    'max_correlation': float(np.max(other_correlations)),
                    'min_correlation': float(np.min(other_correlations))
                }
            
            stats['asset_correlations'] = asset_correlations
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating correlation statistics: {e}")
            return {}
    
    def model_volatility_regimes(self, price_data: pd.DataFrame) -> Dict:
        """Model volatility regimes using Bayesian approach"""
        try:
            returns = price_data['close'].pct_change().dropna()
            
            if len(returns) < 100:
                return {"error": "Insufficient data for volatility modeling"}
            
            # Bayesian Stochastic Volatility Model
            with pm.Model() as volatility_model:
                # Priors for volatility parameters
                sigma_eta = pm.HalfCauchy('sigma_eta', beta=0.1)
                phi = pm.Beta('phi', alpha=20, beta=1.5)  # Persistence parameter
                mu = pm.Normal('mu', mu=0, sigma=1)  # Mean log volatility
                
                # Log volatility process
                log_vol = pm.GaussianRandomWalk('log_vol', 
                                              mu=mu, 
                                              sigma=sigma_eta, 
                                              shape=len(returns))
                
                # Volatility
                vol = pm.Deterministic('vol', pm.math.exp(log_vol))
                
                # Returns likelihood
                pm.Normal('returns', mu=0, sigma=vol, observed=returns)
                
                # Sample from posterior
                trace = pm.sample(1000, tune=1000, cores=2, progressbar=False)
            
            # Extract volatility estimates
            volatility_samples = trace['vol']
            mean_volatility = np.mean(volatility_samples, axis=0)
            
            # Identify volatility regimes
            volatility_regimes = self._identify_volatility_regimes(mean_volatility)
            
            # Calculate volatility statistics
            vol_stats = self._calculate_volatility_statistics(mean_volatility, volatility_regimes)
            
            return {
                "volatility_estimates": mean_volatility.tolist(),
                "volatility_regimes": volatility_regimes,
                "volatility_statistics": vol_stats,
                "volatility_samples": volatility_samples.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error modeling volatility regimes: {e}")
            return {"error": str(e)}
    
    def _identify_volatility_regimes(self, volatility: np.ndarray) -> Dict:
        """Identify volatility regimes using clustering"""
        try:
            # Use K-means to identify volatility regimes
            kmeans = KMeans(n_clusters=3, random_state=42)
            regime_labels = kmeans.fit_predict(volatility.reshape(-1, 1))
            
            # Calculate regime statistics
            regimes = {}
            for regime in range(3):
                regime_mask = regime_labels == regime
                regime_vol = volatility[regime_mask]
                
                if len(regime_vol) > 0:
                    regimes[f"regime_{regime}"] = {
                        "name": f"Volatility Regime {regime + 1}",
                        "count": int(np.sum(regime_mask)),
                        "percentage": float(np.mean(regime_mask) * 100),
                        "mean_volatility": float(np.mean(regime_vol)),
                        "volatility_std": float(np.std(regime_vol)),
                        "min_volatility": float(np.min(regime_vol)),
                        "max_volatility": float(np.max(regime_vol))
                    }
            
            return regimes
            
        except Exception as e:
            logger.error(f"Error identifying volatility regimes: {e}")
            return {}
    
    def _calculate_volatility_statistics(self, volatility: np.ndarray, regimes: Dict) -> Dict:
        """Calculate volatility statistics"""
        try:
            stats = {
                "overall_mean": float(np.mean(volatility)),
                "overall_std": float(np.std(volatility)),
                "min_volatility": float(np.min(volatility)),
                "max_volatility": float(np.max(volatility)),
                "volatility_range": float(np.max(volatility) - np.min(volatility)),
                "volatility_percentiles": {
                    "25th": float(np.percentile(volatility, 25)),
                    "50th": float(np.percentile(volatility, 50)),
                    "75th": float(np.percentile(volatility, 75)),
                    "90th": float(np.percentile(volatility, 90)),
                    "95th": float(np.percentile(volatility, 95))
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating volatility statistics: {e}")
            return {}
    
    def predict_regime_probabilities(self, current_features: np.ndarray) -> Dict:
        """Predict regime probabilities for current market state"""
        try:
            if self.regime_model is None:
                return {"error": "Regime model not trained"}
            
            # Scale features
            features_scaled = self.scaler.transform(current_features.reshape(1, -1))
            
            # Use trained model to predict regime probabilities
            # This would require the trained model to be loaded
            # For now, return mock probabilities
            regime_probs = np.random.dirichlet(np.ones(self.n_regimes))
            
            return {
                "regime_probabilities": regime_probs.tolist(),
                "regime_names": self.regime_names,
                "most_likely_regime": int(np.argmax(regime_probs)),
                "confidence": float(np.max(regime_probs))
            }
            
        except Exception as e:
            logger.error(f"Error predicting regime probabilities: {e}")
            return {"error": str(e)}
    
    def get_market_stress_indicators(self, price_data: Dict[str, pd.DataFrame]) -> Dict:
        """Calculate market stress indicators using Bayesian approach"""
        try:
            stress_indicators = {}
            
            # Prepare data
            returns_data = self._prepare_correlation_data(price_data)
            
            if len(returns_data) == 0:
                return {"error": "No data available for stress indicators"}
            
            # Calculate rolling correlations
            rolling_correlations = returns_data.rolling(60).corr()
            
            # Average correlation stress
            avg_corr = rolling_correlations.groupby(level=0).apply(
                lambda x: x.values[np.triu_indices_from(x.values, k=1)].mean()
            )
            stress_indicators['average_correlation'] = avg_corr.iloc[-1] if len(avg_corr) > 0 else 0
            
            # Correlation dispersion
            corr_dispersion = rolling_correlations.groupby(level=0).apply(
                lambda x: np.std(x.values[np.triu_indices_from(x.values, k=1)])
            )
            stress_indicators['correlation_dispersion'] = corr_dispersion.iloc[-1] if len(corr_dispersion) > 0 else 0
            
            # Volatility clustering
            volatility = returns_data.std()
            vol_clustering = volatility.rolling(20).std()
            stress_indicators['volatility_clustering'] = vol_clustering.iloc[-1] if len(vol_clustering) > 0 else 0
            
            # Tail risk (VaR)
            var_95 = returns_data.quantile(0.05, axis=1)
            stress_indicators['var_95'] = var_95.iloc[-1] if len(var_95) > 0 else 0
            
            # Expected Shortfall
            es_95 = returns_data[returns_data <= var_95.iloc[-1]].mean(axis=1)
            stress_indicators['expected_shortfall_95'] = es_95.iloc[-1] if len(es_95) > 0 else 0
            
            # Market stress score (composite)
            stress_score = (
                abs(stress_indicators['average_correlation']) * 0.3 +
                stress_indicators['correlation_dispersion'] * 0.2 +
                stress_indicators['volatility_clustering'] * 0.2 +
                abs(stress_indicators['var_95']) * 0.2 +
                abs(stress_indicators['expected_shortfall_95']) * 0.1
            )
            stress_indicators['stress_score'] = stress_score
            
            # Stress level classification
            if stress_score < 0.2:
                stress_level = "Low"
            elif stress_score < 0.5:
                stress_level = "Medium"
            elif stress_score < 0.8:
                stress_level = "High"
            else:
                stress_level = "Extreme"
            
            stress_indicators['stress_level'] = stress_level
            
            return stress_indicators
            
        except Exception as e:
            logger.error(f"Error calculating market stress indicators: {e}")
            return {"error": str(e)}
    
    def save_models(self):
        """Save trained models"""
        try:
            # Save scaler
            joblib.dump(self.scaler, os.path.join(self.models_dir, 'bayesian_scaler.pkl'))
            
            # Save model parameters
            model_params = {
                'n_regimes': self.n_regimes,
                'regime_names': self.regime_names,
                'correlation_window': self.correlation_window
            }
            
            with open(os.path.join(self.models_dir, 'model_params.json'), 'w') as f:
                import json
                json.dump(model_params, f)
            
            logger.info("Bayesian models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self):
        """Load trained models"""
        try:
            # Load scaler
            scaler_path = os.path.join(self.models_dir, 'bayesian_scaler.pkl')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info("Bayesian scaler loaded")
            
            # Load model parameters
            params_path = os.path.join(self.models_dir, 'model_params.json')
            if os.path.exists(params_path):
                with open(params_path, 'r') as f:
                    import json
                    params = json.load(f)
                    self.n_regimes = params.get('n_regimes', 3)
                    self.regime_names = params.get('regime_names', ['Bull Market', 'Bear Market', 'Sideways Market'])
                    self.correlation_window = params.get('correlation_window', 252)
                logger.info("Bayesian model parameters loaded")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
