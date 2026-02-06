"""
Alternative Data Models Service
Transformer and CNN models for NLP sentiment and on-chain data analysis
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
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import os
import math
import json

logger = logging.getLogger(__name__)

class AlternativeDataDataset(Dataset):
    """Dataset for alternative data (NLP + On-chain)"""
    
    def __init__(self, text_features, onchain_features, targets, max_text_length=512):
        self.text_features = text_features
        self.onchain_features = onchain_features
        self.targets = targets
        self.max_text_length = max_text_length
    
    def __len__(self):
        return len(self.text_features)
    
    def __getitem__(self, idx):
        text_feat = torch.FloatTensor(self.text_features[idx])
        onchain_feat = torch.FloatTensor(self.onchain_features[idx])
        target = torch.FloatTensor(self.targets[idx])
        
        return {
            'text_features': text_feat,
            'onchain_features': onchain_feat,
            'target': target
        }

class TextCNN(nn.Module):
    """CNN model for text sentiment analysis"""
    
    def __init__(self, vocab_size, embed_dim=128, num_filters=100, filter_sizes=[3, 4, 5], dropout=0.5):
        super(TextCNN, self).__init__()
        
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.convs = nn.ModuleList([
            nn.Conv1d(embed_dim, num_filters, kernel_size=fs)
            for fs in filter_sizes
        ])
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(len(filter_sizes) * num_filters, 1)
        
    def forward(self, x):
        # x shape: (batch_size, seq_len)
        embedded = self.embedding(x)  # (batch_size, seq_len, embed_dim)
        embedded = embedded.permute(0, 2, 1)  # (batch_size, embed_dim, seq_len)
        
        conv_outputs = []
        for conv in self.convs:
            conv_out = torch.relu(conv(embedded))  # (batch_size, num_filters, conv_seq_len)
            pooled = torch.max_pool1d(conv_out, kernel_size=conv_out.size(2))  # (batch_size, num_filters, 1)
            conv_outputs.append(pooled.squeeze(2))  # (batch_size, num_filters)
        
        concatenated = torch.cat(conv_outputs, dim=1)  # (batch_size, len(filter_sizes) * num_filters)
        output = self.fc(self.dropout(concatenated))
        
        return output

class OnChainTransformer(nn.Module):
    """Transformer model for on-chain data analysis"""
    
    def __init__(self, input_dim, d_model=128, nhead=8, num_layers=4, output_dim=1, dropout=0.1):
        super(OnChainTransformer, self).__init__()
        
        self.input_projection = nn.Linear(input_dim, d_model)
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
        self.fc3 = nn.Linear(32, output_dim)
        
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

class MultiModalTransformer(nn.Module):
    """Multi-modal transformer combining text and on-chain data"""
    
    def __init__(self, text_vocab_size, onchain_dim, d_model=128, nhead=8, num_layers=4, output_dim=1, dropout=0.1):
        super(MultiModalTransformer, self).__init__()
        
        # Text processing
        self.text_embedding = nn.Embedding(text_vocab_size, d_model)
        self.text_projection = nn.Linear(d_model, d_model)
        
        # On-chain processing
        self.onchain_projection = nn.Linear(onchain_dim, d_model)
        
        # Positional encoding
        self.positional_encoding = PositionalEncoding(d_model, dropout)
        
        # Cross-attention layers
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=nhead,
            dropout=dropout,
            batch_first=True
        )
        
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
        self.fc1 = nn.Linear(d_model * 2, 128)  # *2 for concatenated features
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, output_dim)
        
        self.dropout = nn.Dropout(dropout)
        self.relu = nn.ReLU()
        
    def forward(self, text_features, onchain_features):
        # Process text features
        text_embedded = self.text_embedding(text_features)
        text_projected = self.text_projection(text_embedded)
        
        # Process on-chain features
        onchain_projected = self.onchain_projection(onchain_features)
        
        # Add positional encoding
        text_projected = self.positional_encoding(text_projected)
        onchain_projected = self.positional_encoding(onchain_projected)
        
        # Cross-attention between text and on-chain features
        text_attended, _ = self.cross_attention(text_projected, onchain_projected, onchain_projected)
        onchain_attended, _ = self.cross_attention(onchain_projected, text_projected, text_projected)
        
        # Combine features
        combined_features = torch.cat([text_attended, onchain_attended], dim=-1)
        
        # Global average pooling
        pooled = torch.mean(combined_features, dim=1)
        
        # Fully connected layers
        x = self.dropout(self.relu(self.fc1(pooled)))
        x = self.dropout(self.relu(self.fc2(x)))
        x = self.fc3(x)
        
        return x

class AlternativeDataModels:
    """Alternative data models for NLP sentiment and on-chain analysis"""
    
    def __init__(self):
        self.text_cnn_model = None
        self.onchain_transformer = None
        self.multimodal_transformer = None
        
        # Feature processors
        self.text_vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
        self.text_scaler = StandardScaler()
        self.onchain_scaler = StandardScaler()
        
        # Models directory
        self.models_dir = "models/alternative_data"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Training parameters
        self.batch_size = 32
        self.learning_rate = 0.001
        self.num_epochs = 100
        self.patience = 10
        
    def prepare_text_features(self, texts: List[str]) -> Tuple[np.ndarray, Dict]:
        """Prepare text features for models"""
        try:
            if not texts:
                return np.array([]), {}
            
            # Extract NLP features
            from services.advanced_nlp_features import AdvancedNLPFeatures
            nlp_processor = AdvancedNLPFeatures()
            
            text_features = []
            for text in texts:
                features = nlp_processor.extract_comprehensive_features(text)
                text_features.append(features)
            
            # Convert to DataFrame
            df = pd.DataFrame(text_features)
            df = df.fillna(0)
            
            # Select numeric features
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            text_features_array = df[numeric_cols].values
            
            # Scale features
            text_features_scaled = self.text_scaler.fit_transform(text_features_array)
            
            # Create vocabulary for CNN
            vocab = self._create_vocabulary(texts)
            
            return text_features_scaled, {
                'vocab': vocab,
                'feature_names': numeric_cols.tolist(),
                'vocab_size': len(vocab)
            }
            
        except Exception as e:
            logger.error(f"Error preparing text features: {e}")
            return np.array([]), {}
    
    def prepare_onchain_features(self, onchain_data: List[Dict]) -> np.ndarray:
        """Prepare on-chain features for models"""
        try:
            if not onchain_data:
                return np.array([])
            
            # Extract features from on-chain data
            features = []
            for data in onchain_data:
                feature_vector = []
                
                # Market metrics
                coingecko = data.get('coingecko', {})
                feature_vector.extend([
                    coingecko.get('market_cap', 0),
                    coingecko.get('trading_volume', 0),
                    coingecko.get('price_change_24h', 0),
                    coingecko.get('price_change_7d', 0),
                    coingecko.get('price_change_30d', 0)
                ])
                
                # Glassnode metrics
                glassnode = data.get('glassnode', {})
                feature_vector.extend([
                    glassnode.get('active_addresses', 0),
                    glassnode.get('transaction_count', 0),
                    glassnode.get('mvrv_ratio', 0),
                    glassnode.get('nvt_ratio', 0),
                    glassnode.get('supply_in_profit', 0)
                ])
                
                features.append(feature_vector)
            
            features_array = np.array(features)
            
            # Scale features
            features_scaled = self.onchain_scaler.fit_transform(features_array)
            
            return features_scaled
            
        except Exception as e:
            logger.error(f"Error preparing on-chain features: {e}")
            return np.array([])
    
    def _create_vocabulary(self, texts: List[str]) -> Dict[str, int]:
        """Create vocabulary from texts"""
        try:
            vocab = {}
            word_id = 1  # Start from 1, 0 is reserved for padding
            
            for text in texts:
                words = text.lower().split()
                for word in words:
                    if word not in vocab:
                        vocab[word] = word_id
                        word_id += 1
            
            return vocab
        except Exception as e:
            logger.error(f"Error creating vocabulary: {e}")
            return {}
    
    def _text_to_sequences(self, texts: List[str], vocab: Dict[str, int], max_length: int = 512) -> np.ndarray:
        """Convert texts to sequences of word indices"""
        try:
            sequences = []
            for text in texts:
                words = text.lower().split()
                sequence = [vocab.get(word, 0) for word in words[:max_length]]
                
                # Pad sequences
                if len(sequence) < max_length:
                    sequence.extend([0] * (max_length - len(sequence)))
                
                sequences.append(sequence)
            
            return np.array(sequences)
        except Exception as e:
            logger.error(f"Error converting texts to sequences: {e}")
            return np.array([])
    
    def train_text_cnn(self, texts: List[str], targets: np.ndarray) -> Dict:
        """Train CNN model for text sentiment analysis"""
        try:
            # Prepare text features
            text_features, text_info = self.prepare_text_features(texts)
            if len(text_features) == 0:
                return {"error": "No text features available"}
            
            # Convert texts to sequences
            vocab = text_info['vocab']
            sequences = self._text_to_sequences(texts, vocab)
            
            if len(sequences) == 0:
                return {"error": "No sequences available"}
            
            # Split data
            split_idx = int(0.8 * len(sequences))
            X_train, X_val = sequences[:split_idx], sequences[split_idx:]
            y_train, y_val = targets[:split_idx], targets[split_idx:]
            
            # Create datasets
            train_dataset = TextSequenceDataset(X_train, y_train)
            val_dataset = TextSequenceDataset(X_val, y_val)
            
            train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)
            
            # Initialize model
            vocab_size = len(vocab) + 1  # +1 for padding
            self.text_cnn_model = TextCNN(vocab_size=vocab_size)
            
            # Training setup
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.text_cnn_model.parameters(), lr=self.learning_rate)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
            
            # Training loop
            best_val_loss = float('inf')
            patience_counter = 0
            
            for epoch in range(self.num_epochs):
                # Training
                self.text_cnn_model.train()
                train_loss = 0
                for batch_X, batch_y in train_loader:
                    optimizer.zero_grad()
                    outputs = self.text_cnn_model(batch_X)
                    loss = criterion(outputs.squeeze(), batch_y)
                    loss.backward()
                    optimizer.step()
                    train_loss += loss.item()
                
                # Validation
                self.text_cnn_model.eval()
                val_loss = 0
                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        outputs = self.text_cnn_model(batch_X)
                        loss = criterion(outputs.squeeze(), batch_y)
                        val_loss += loss.item()
                
                train_loss /= len(train_loader)
                val_loss /= len(val_loader)
                
                scheduler.step(val_loss)
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    torch.save(self.text_cnn_model.state_dict(), 
                             os.path.join(self.models_dir, 'text_cnn_best.pth'))
                else:
                    patience_counter += 1
                
                if patience_counter >= self.patience:
                    break
                
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}, Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
            
            # Load best model
            self.text_cnn_model.load_state_dict(torch.load(os.path.join(self.models_dir, 'text_cnn_best.pth')))
            
            # Save vocabulary
            with open(os.path.join(self.models_dir, 'text_vocab.json'), 'w') as f:
                json.dump(vocab, f)
            
            return {
                "status": "success",
                "final_train_loss": train_loss,
                "final_val_loss": val_loss,
                "best_val_loss": best_val_loss,
                "vocab_size": vocab_size
            }
            
        except Exception as e:
            logger.error(f"Error training text CNN: {e}")
            return {"error": str(e)}
    
    def train_onchain_transformer(self, onchain_data: List[Dict], targets: np.ndarray) -> Dict:
        """Train Transformer model for on-chain data"""
        try:
            # Prepare on-chain features
            onchain_features = self.prepare_onchain_features(onchain_data)
            if len(onchain_features) == 0:
                return {"error": "No on-chain features available"}
            
            # Split data
            split_idx = int(0.8 * len(onchain_features))
            X_train, X_val = onchain_features[:split_idx], onchain_features[split_idx:]
            y_train, y_val = targets[:split_idx], targets[split_idx:]
            
            # Create datasets
            train_dataset = OnChainDataset(X_train, y_train)
            val_dataset = OnChainDataset(X_val, y_val)
            
            train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)
            
            # Initialize model
            input_dim = onchain_features.shape[1]
            self.onchain_transformer = OnChainTransformer(input_dim=input_dim)
            
            # Training setup
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.onchain_transformer.parameters(), lr=self.learning_rate)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
            
            # Training loop
            best_val_loss = float('inf')
            patience_counter = 0
            
            for epoch in range(self.num_epochs):
                # Training
                self.onchain_transformer.train()
                train_loss = 0
                for batch_X, batch_y in train_loader:
                    optimizer.zero_grad()
                    outputs = self.onchain_transformer(batch_X)
                    loss = criterion(outputs.squeeze(), batch_y)
                    loss.backward()
                    optimizer.step()
                    train_loss += loss.item()
                
                # Validation
                self.onchain_transformer.eval()
                val_loss = 0
                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        outputs = self.onchain_transformer(batch_X)
                        loss = criterion(outputs.squeeze(), batch_y)
                        val_loss += loss.item()
                
                train_loss /= len(train_loader)
                val_loss /= len(val_loader)
                
                scheduler.step(val_loss)
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    torch.save(self.onchain_transformer.state_dict(), 
                             os.path.join(self.models_dir, 'onchain_transformer_best.pth'))
                else:
                    patience_counter += 1
                
                if patience_counter >= self.patience:
                    break
                
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}, Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
            
            # Load best model
            self.onchain_transformer.load_state_dict(torch.load(os.path.join(self.models_dir, 'onchain_transformer_best.pth')))
            
            return {
                "status": "success",
                "final_train_loss": train_loss,
                "final_val_loss": val_loss,
                "best_val_loss": best_val_loss,
                "input_dim": input_dim
            }
            
        except Exception as e:
            logger.error(f"Error training on-chain transformer: {e}")
            return {"error": str(e)}
    
    def train_multimodal_transformer(self, texts: List[str], onchain_data: List[Dict], targets: np.ndarray) -> Dict:
        """Train multi-modal transformer combining text and on-chain data"""
        try:
            # Prepare features
            text_features, text_info = self.prepare_text_features(texts)
            onchain_features = self.prepare_onchain_features(onchain_data)
            
            if len(text_features) == 0 or len(onchain_features) == 0:
                return {"error": "Insufficient features for training"}
            
            # Convert texts to sequences
            vocab = text_info['vocab']
            sequences = self._text_to_sequences(texts, vocab)
            
            if len(sequences) == 0:
                return {"error": "No text sequences available"}
            
            # Ensure same length
            min_len = min(len(sequences), len(onchain_features), len(targets))
            sequences = sequences[:min_len]
            onchain_features = onchain_features[:min_len]
            targets = targets[:min_len]
            
            # Split data
            split_idx = int(0.8 * min_len)
            text_train, text_val = sequences[:split_idx], sequences[split_idx:]
            onchain_train, onchain_val = onchain_features[:split_idx], onchain_features[split_idx:]
            y_train, y_val = targets[:split_idx], targets[split_idx:]
            
            # Create datasets
            train_dataset = MultiModalDataset(text_train, onchain_train, y_train)
            val_dataset = MultiModalDataset(text_val, onchain_val, y_val)
            
            train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)
            
            # Initialize model
            vocab_size = len(vocab) + 1
            onchain_dim = onchain_features.shape[1]
            self.multimodal_transformer = MultiModalTransformer(
                text_vocab_size=vocab_size,
                onchain_dim=onchain_dim
            )
            
            # Training setup
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.multimodal_transformer.parameters(), lr=self.learning_rate)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
            
            # Training loop
            best_val_loss = float('inf')
            patience_counter = 0
            
            for epoch in range(self.num_epochs):
                # Training
                self.multimodal_transformer.train()
                train_loss = 0
                for batch in train_loader:
                    optimizer.zero_grad()
                    outputs = self.multimodal_transformer(
                        batch['text_features'], 
                        batch['onchain_features']
                    )
                    loss = criterion(outputs.squeeze(), batch['target'])
                    loss.backward()
                    optimizer.step()
                    train_loss += loss.item()
                
                # Validation
                self.multimodal_transformer.eval()
                val_loss = 0
                with torch.no_grad():
                    for batch in val_loader:
                        outputs = self.multimodal_transformer(
                            batch['text_features'], 
                            batch['onchain_features']
                        )
                        loss = criterion(outputs.squeeze(), batch['target'])
                        val_loss += loss.item()
                
                train_loss /= len(train_loader)
                val_loss /= len(val_loader)
                
                scheduler.step(val_loss)
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    torch.save(self.multimodal_transformer.state_dict(), 
                             os.path.join(self.models_dir, 'multimodal_transformer_best.pth'))
                else:
                    patience_counter += 1
                
                if patience_counter >= self.patience:
                    break
                
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}, Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
            
            # Load best model
            self.multimodal_transformer.load_state_dict(torch.load(os.path.join(self.models_dir, 'multimodal_transformer_best.pth')))
            
            return {
                "status": "success",
                "final_train_loss": train_loss,
                "final_val_loss": val_loss,
                "best_val_loss": best_val_loss,
                "vocab_size": vocab_size,
                "onchain_dim": onchain_dim
            }
            
        except Exception as e:
            logger.error(f"Error training multi-modal transformer: {e}")
            return {"error": str(e)}
    
    def predict_sentiment(self, texts: List[str]) -> Dict:
        """Predict sentiment using text CNN"""
        try:
            if self.text_cnn_model is None:
                return {"error": "Text CNN model not trained"}
            
            # Load vocabulary
            vocab_path = os.path.join(self.models_dir, 'text_vocab.json')
            if not os.path.exists(vocab_path):
                return {"error": "Vocabulary not found"}
            
            with open(vocab_path, 'r') as f:
                vocab = json.load(f)
            
            # Convert texts to sequences
            sequences = self._text_to_sequences(texts, vocab)
            if len(sequences) == 0:
                return {"error": "No sequences generated"}
            
            # Make predictions
            self.text_cnn_model.eval()
            predictions = []
            
            with torch.no_grad():
                for i in range(len(sequences)):
                    x = torch.LongTensor(sequences[i:i+1])
                    pred = self.text_cnn_model(x)
                    predictions.append(pred.item())
            
            return {
                "predictions": predictions,
                "model_type": "Text CNN",
                "n_texts": len(texts)
            }
            
        except Exception as e:
            logger.error(f"Error predicting sentiment: {e}")
            return {"error": str(e)}
    
    def predict_onchain(self, onchain_data: List[Dict]) -> Dict:
        """Predict using on-chain transformer"""
        try:
            if self.onchain_transformer is None:
                return {"error": "On-chain transformer not trained"}
            
            # Prepare features
            onchain_features = self.prepare_onchain_features(onchain_data)
            if len(onchain_features) == 0:
                return {"error": "No on-chain features available"}
            
            # Make predictions
            self.onchain_transformer.eval()
            predictions = []
            
            with torch.no_grad():
                for i in range(len(onchain_features)):
                    x = torch.FloatTensor(onchain_features[i:i+1])
                    pred = self.onchain_transformer(x)
                    predictions.append(pred.item())
            
            return {
                "predictions": predictions,
                "model_type": "On-chain Transformer",
                "n_samples": len(onchain_data)
            }
            
        except Exception as e:
            logger.error(f"Error predicting on-chain: {e}")
            return {"error": str(e)}
    
    def predict_multimodal(self, texts: List[str], onchain_data: List[Dict]) -> Dict:
        """Predict using multi-modal transformer"""
        try:
            if self.multimodal_transformer is None:
                return {"error": "Multi-modal transformer not trained"}
            
            # Load vocabulary
            vocab_path = os.path.join(self.models_dir, 'text_vocab.json')
            if not os.path.exists(vocab_path):
                return {"error": "Vocabulary not found"}
            
            with open(vocab_path, 'r') as f:
                vocab = json.load(f)
            
            # Prepare features
            onchain_features = self.prepare_onchain_features(onchain_data)
            sequences = self._text_to_sequences(texts, vocab)
            
            if len(onchain_features) == 0 or len(sequences) == 0:
                return {"error": "Insufficient features for prediction"}
            
            # Ensure same length
            min_len = min(len(sequences), len(onchain_features))
            sequences = sequences[:min_len]
            onchain_features = onchain_features[:min_len]
            
            # Make predictions
            self.multimodal_transformer.eval()
            predictions = []
            
            with torch.no_grad():
                for i in range(min_len):
                    text_seq = torch.LongTensor(sequences[i:i+1])
                    onchain_feat = torch.FloatTensor(onchain_features[i:i+1])
                    pred = self.multimodal_transformer(text_seq, onchain_feat)
                    predictions.append(pred.item())
            
            return {
                "predictions": predictions,
                "model_type": "Multi-modal Transformer",
                "n_samples": min_len
            }
            
        except Exception as e:
            logger.error(f"Error predicting multi-modal: {e}")
            return {"error": str(e)}

# Helper dataset classes
class TextSequenceDataset(Dataset):
    def __init__(self, sequences, targets):
        self.sequences = sequences
        self.targets = targets
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return torch.LongTensor(self.sequences[idx]), torch.FloatTensor(self.targets[idx])

class OnChainDataset(Dataset):
    def __init__(self, features, targets):
        self.features = features
        self.targets = targets
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return torch.FloatTensor(self.features[idx]), torch.FloatTensor(self.targets[idx])

class MultiModalDataset(Dataset):
    def __init__(self, text_sequences, onchain_features, targets):
        self.text_sequences = text_sequences
        self.onchain_features = onchain_features
        self.targets = targets
    
    def __len__(self):
        return len(self.text_sequences)
    
    def __getitem__(self, idx):
        return {
            'text_features': torch.LongTensor(self.text_sequences[idx]),
            'onchain_features': torch.FloatTensor(self.onchain_features[idx]),
            'target': torch.FloatTensor(self.targets[idx])
        }
