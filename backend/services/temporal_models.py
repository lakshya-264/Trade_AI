"""
Temporal Models Service
Transformer and LSTM models for raw price sequence analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import os
import math

logger = logging.getLogger(__name__)

class PriceSequenceDataset(Dataset):
    """Dataset for price sequence data"""
    
    def __init__(self, sequences, targets, sequence_length=60):
        self.sequences = sequences
        self.targets = targets
        self.sequence_length = sequence_length
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return torch.FloatTensor(self.sequences[idx]), torch.FloatTensor(self.targets[idx])

class LSTMPricePredictor(nn.Module):
    """LSTM model for price sequence prediction"""
    
    def __init__(self, input_size=5, hidden_size=128, num_layers=2, output_size=1, dropout=0.2):
        super(LSTMPricePredictor, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=8,
            dropout=dropout,
            batch_first=True
        )
        
        # Output layers
        self.fc1 = nn.Linear(hidden_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, output_size)
        
        self.dropout = nn.Dropout(dropout)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        batch_size = x.size(0)
        
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size)
        
        # LSTM forward pass
        lstm_out, (hn, cn) = self.lstm(x, (h0, c0))
        
        # Apply attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Global average pooling
        pooled = torch.mean(attn_out, dim=1)
        
        # Fully connected layers
        x = self.dropout(self.relu(self.fc1(pooled)))
        x = self.dropout(self.relu(self.fc2(x)))
        x = self.fc3(x)
        
        return x

class TransformerPricePredictor(nn.Module):
    """Transformer model for price sequence prediction"""
    
    def __init__(self, input_size=5, d_model=128, nhead=8, num_layers=4, output_size=1, dropout=0.1):
        super(TransformerPricePredictor, self).__init__()
        
        self.d_model = d_model
        self.input_projection = nn.Linear(input_size, d_model)
        self.positional_encoding = PositionalEncoding(d_model, dropout)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=512,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output layers
        self.fc1 = nn.Linear(d_model, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, output_size)
        
        self.dropout = nn.Dropout(dropout)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        # Project input to model dimension
        x = self.input_projection(x)
        
        # Add positional encoding
        x = self.positional_encoding(x)
        
        # Transformer forward pass
        transformer_out = self.transformer(x)
        
        # Global average pooling
        pooled = torch.mean(transformer_out, dim=1)
        
        # Fully connected layers
        x = self.dropout(self.relu(self.fc1(pooled)))
        x = self.dropout(self.relu(self.fc2(x)))
        x = self.fc3(x)
        
        return x

class PositionalEncoding(nn.Module):
    """Positional encoding for transformer"""
    
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

class TemporalModels:
    """Temporal models service for price sequence analysis"""
    
    def __init__(self):
        self.lstm_model = None
        self.transformer_model = None
        self.scaler = MinMaxScaler()
        self.sequence_length = 60
        self.prediction_horizon = 1
        
        # Model paths
        self.models_dir = "models/temporal"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Training parameters
        self.batch_size = 32
        self.learning_rate = 0.001
        self.num_epochs = 100
        self.patience = 10
        
    def prepare_sequences(self, df: pd.DataFrame, features: List[str] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for temporal models"""
        try:
            if features is None:
                features = ['open', 'high', 'low', 'close', 'volume']
            
            # Select and scale features
            data = df[features].values
            scaled_data = self.scaler.fit_transform(data)
            
            # Create sequences
            X, y = [], []
            for i in range(self.sequence_length, len(scaled_data) - self.prediction_horizon + 1):
                X.append(scaled_data[i-self.sequence_length:i])
                # Ensure y is a scalar value (not array)
                y_value = float(scaled_data[i+self.prediction_horizon-1, 3])  # Close price
                y.append(y_value)
            
            y_array = np.array(y)
            # Ensure y is 1D array for the dataset
            if len(y_array.shape) > 1:
                y_array = y_array.flatten()
            return np.array(X), y_array
            
        except Exception as e:
            logger.error(f"Error preparing sequences: {e}")
            return np.array([]), np.array([])
    
    def train_lstm_model(self, df: pd.DataFrame, features: List[str] = None) -> Dict:
        """Train LSTM model on price sequences"""
        try:
            # Prepare data
            X, y = self.prepare_sequences(df, features)
            if len(X) == 0:
                return {"error": "No data available for training"}
            
            # Split data
            split_idx = int(0.8 * len(X))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Ensure y is properly formatted (1D array)
            y_train = y_train.flatten() if len(y_train.shape) > 1 else y_train
            y_val = y_val.flatten() if len(y_val.shape) > 1 else y_val
            
            # Create datasets
            train_dataset = PriceSequenceDataset(X_train, y_train, self.sequence_length)
            val_dataset = PriceSequenceDataset(X_val, y_val, self.sequence_length)
            
            train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)
            
            # Initialize model
            input_size = X.shape[2]
            self.lstm_model = LSTMPricePredictor(
                input_size=input_size,
                hidden_size=128,
                num_layers=2,
                output_size=1,
                dropout=0.2
            )
            
            # Training setup
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.lstm_model.parameters(), lr=self.learning_rate)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
            
            # Training loop
            best_val_loss = float('inf')
            patience_counter = 0
            train_losses = []
            val_losses = []
            
            for epoch in range(self.num_epochs):
                # Training
                self.lstm_model.train()
                train_loss = 0
                for batch_X, batch_y in train_loader:
                    optimizer.zero_grad()
                    outputs = self.lstm_model(batch_X)
                    loss = criterion(outputs.squeeze(), batch_y)
                    loss.backward()
                    optimizer.step()
                    train_loss += loss.item()
                
                # Validation
                self.lstm_model.eval()
                val_loss = 0
                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        outputs = self.lstm_model(batch_X)
                        loss = criterion(outputs.squeeze(), batch_y)
                        val_loss += loss.item()
                
                train_loss /= len(train_loader)
                val_loss /= len(val_loader)
                
                train_losses.append(train_loss)
                val_losses.append(val_loss)
                
                # Learning rate scheduling
                scheduler.step(val_loss)
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    # Save best model
                    torch.save(self.lstm_model.state_dict(), 
                             os.path.join(self.models_dir, 'lstm_best_model.pth'))
                else:
                    patience_counter += 1
                
                if patience_counter >= self.patience:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
                
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}, Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
            
            # Load best model
            self.lstm_model.load_state_dict(torch.load(os.path.join(self.models_dir, 'lstm_best_model.pth')))
            
            # Save scaler
            joblib.dump(self.scaler, os.path.join(self.models_dir, 'lstm_scaler.pkl'))
            
            return {
                "status": "success",
                "final_train_loss": train_losses[-1],
                "final_val_loss": val_losses[-1],
                "best_val_loss": best_val_loss,
                "epochs_trained": len(train_losses)
            }
            
        except Exception as e:
            logger.error(f"Error training LSTM model: {e}")
            return {"error": str(e)}
    
    def train_transformer_model(self, df: pd.DataFrame, features: List[str] = None) -> Dict:
        """Train Transformer model on price sequences"""
        try:
            # Prepare data
            X, y = self.prepare_sequences(df, features)
            if len(X) == 0:
                return {"error": "No data available for training"}
            
            # Split data
            split_idx = int(0.8 * len(X))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Ensure y is properly formatted (1D array)
            y_train = y_train.flatten() if len(y_train.shape) > 1 else y_train
            y_val = y_val.flatten() if len(y_val.shape) > 1 else y_val
            
            # Create datasets
            train_dataset = PriceSequenceDataset(X_train, y_train, self.sequence_length)
            val_dataset = PriceSequenceDataset(X_val, y_val, self.sequence_length)
            
            train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)
            
            # Initialize model
            input_size = X.shape[2]
            self.transformer_model = TransformerPricePredictor(
                input_size=input_size,
                d_model=128,
                nhead=8,
                num_layers=4,
                output_size=1,
                dropout=0.1
            )
            
            # Training setup
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.transformer_model.parameters(), lr=self.learning_rate)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
            
            # Training loop
            best_val_loss = float('inf')
            patience_counter = 0
            train_losses = []
            val_losses = []
            
            for epoch in range(self.num_epochs):
                # Training
                self.transformer_model.train()
                train_loss = 0
                for batch_X, batch_y in train_loader:
                    optimizer.zero_grad()
                    outputs = self.transformer_model(batch_X)
                    loss = criterion(outputs.squeeze(), batch_y)
                    loss.backward()
                    optimizer.step()
                    train_loss += loss.item()
                
                # Validation
                self.transformer_model.eval()
                val_loss = 0
                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        outputs = self.transformer_model(batch_X)
                        loss = criterion(outputs.squeeze(), batch_y)
                        val_loss += loss.item()
                
                train_loss /= len(train_loader)
                val_loss /= len(val_loader)
                
                train_losses.append(train_loss)
                val_losses.append(val_loss)
                
                # Learning rate scheduling
                scheduler.step(val_loss)
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    # Save best model
                    torch.save(self.transformer_model.state_dict(), 
                             os.path.join(self.models_dir, 'transformer_best_model.pth'))
                else:
                    patience_counter += 1
                
                if patience_counter >= self.patience:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
                
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}, Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
            
            # Load best model
            self.transformer_model.load_state_dict(torch.load(os.path.join(self.models_dir, 'transformer_best_model.pth')))
            
            # Save scaler
            joblib.dump(self.scaler, os.path.join(self.models_dir, 'transformer_scaler.pkl'))
            
            return {
                "status": "success",
                "final_train_loss": train_losses[-1],
                "final_val_loss": val_losses[-1],
                "best_val_loss": best_val_loss,
                "epochs_trained": len(train_losses)
            }
            
        except Exception as e:
            logger.error(f"Error training Transformer model: {e}")
            return {"error": str(e)}
    
    def predict_lstm(self, df: pd.DataFrame, features: List[str] = None) -> Dict:
        """Make predictions using LSTM model"""
        try:
            if self.lstm_model is None:
                return {"error": "LSTM model not trained"}
            
            # Prepare data
            X, _ = self.prepare_sequences(df, features)
            if len(X) == 0:
                return {"error": "No data available for prediction"}
            
            # Make predictions
            self.lstm_model.eval()
            predictions = []
            
            with torch.no_grad():
                for i in range(len(X)):
                    x = torch.FloatTensor(X[i:i+1])
                    pred = self.lstm_model(x)
                    predictions.append(pred.item())
            
            # Inverse transform predictions
            predictions = np.array(predictions).reshape(-1, 1)
            dummy_data = np.zeros((len(predictions), self.scaler.n_features_in_))
            dummy_data[:, 3] = predictions.flatten()  # Close price column
            predictions = self.scaler.inverse_transform(dummy_data)[:, 3]
            
            return {
                "predictions": predictions.tolist(),
                "model_type": "LSTM",
                "sequence_length": self.sequence_length
            }
            
        except Exception as e:
            logger.error(f"Error making LSTM predictions: {e}")
            return {"error": str(e)}
    
    def predict_transformer(self, df: pd.DataFrame, features: List[str] = None) -> Dict:
        """Make predictions using Transformer model"""
        try:
            if self.transformer_model is None:
                return {"error": "Transformer model not trained"}
            
            # Prepare data
            X, _ = self.prepare_sequences(df, features)
            if len(X) == 0:
                return {"error": "No data available for prediction"}
            
            # Make predictions
            self.transformer_model.eval()
            predictions = []
            
            with torch.no_grad():
                for i in range(len(X)):
                    x = torch.FloatTensor(X[i:i+1])
                    pred = self.transformer_model(x)
                    predictions.append(pred.item())
            
            # Inverse transform predictions
            predictions = np.array(predictions).reshape(-1, 1)
            dummy_data = np.zeros((len(predictions), self.scaler.n_features_in_))
            dummy_data[:, 3] = predictions.flatten()  # Close price column
            predictions = self.scaler.inverse_transform(dummy_data)[:, 3]
            
            return {
                "predictions": predictions.tolist(),
                "model_type": "Transformer",
                "sequence_length": self.sequence_length
            }
            
        except Exception as e:
            logger.error(f"Error making Transformer predictions: {e}")
            return {"error": str(e)}
    
    def ensemble_predict(self, df: pd.DataFrame, features: List[str] = None) -> Dict:
        """Make ensemble predictions using both models"""
        try:
            lstm_pred = self.predict_lstm(df, features)
            transformer_pred = self.predict_transformer(df, features)
            
            if "error" in lstm_pred or "error" in transformer_pred:
                return {"error": "One or both models failed"}
            
            # Weighted ensemble (can be optimized)
            lstm_weight = 0.6
            transformer_weight = 0.4
            
            ensemble_pred = (
                np.array(lstm_pred["predictions"]) * lstm_weight +
                np.array(transformer_pred["predictions"]) * transformer_weight
            )
            
            return {
                "ensemble_predictions": ensemble_pred.tolist(),
                "lstm_predictions": lstm_pred["predictions"],
                "transformer_predictions": transformer_pred["predictions"],
                "weights": {"lstm": lstm_weight, "transformer": transformer_weight}
            }
            
        except Exception as e:
            logger.error(f"Error making ensemble predictions: {e}")
            return {"error": str(e)}
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            # Load LSTM model
            lstm_path = os.path.join(self.models_dir, 'lstm_best_model.pth')
            if os.path.exists(lstm_path):
                input_size = 5  # Default
                self.lstm_model = LSTMPricePredictor(input_size=input_size)
                self.lstm_model.load_state_dict(torch.load(lstm_path))
                self.lstm_model.eval()
                logger.info("LSTM model loaded successfully")
            
            # Load Transformer model
            transformer_path = os.path.join(self.models_dir, 'transformer_best_model.pth')
            if os.path.exists(transformer_path):
                input_size = 5  # Default
                self.transformer_model = TransformerPricePredictor(input_size=input_size)
                self.transformer_model.load_state_dict(torch.load(transformer_path))
                self.transformer_model.eval()
                logger.info("Transformer model loaded successfully")
            
            # Load scaler
            scaler_path = os.path.join(self.models_dir, 'lstm_scaler.pkl')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info("Scaler loaded successfully")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def get_model_performance(self, df: pd.DataFrame, features: List[str] = None) -> Dict:
        """Evaluate model performance on test data"""
        try:
            # Prepare data
            X, y = self.prepare_sequences(df, features)
            if len(X) == 0:
                return {"error": "No data available for evaluation"}
            
            # Split data (use last 20% for testing)
            split_idx = int(0.8 * len(X))
            X_test, y_test = X[split_idx:], y[split_idx:]
            
            # Get predictions
            lstm_pred = self.predict_lstm(df.iloc[split_idx:], features)
            transformer_pred = self.predict_transformer(df.iloc[split_idx:], features)
            
            if "error" in lstm_pred or "error" in transformer_pred:
                return {"error": "One or both models failed"}
            
            # Calculate metrics
            lstm_mse = mean_squared_error(y_test, lstm_pred["predictions"])
            lstm_mae = mean_absolute_error(y_test, lstm_pred["predictions"])
            
            transformer_mse = mean_squared_error(y_test, transformer_pred["predictions"])
            transformer_mae = mean_absolute_error(y_test, transformer_pred["predictions"])
            
            return {
                "lstm": {
                    "mse": lstm_mse,
                    "mae": lstm_mae,
                    "rmse": np.sqrt(lstm_mse)
                },
                "transformer": {
                    "mse": transformer_mse,
                    "mae": transformer_mae,
                    "rmse": np.sqrt(transformer_mse)
                },
                "test_samples": len(y_test)
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model performance: {e}")
            return {"error": str(e)}
