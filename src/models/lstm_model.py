"""
LSTM model for time series prediction of bin fill levels
"""

import numpy as np
import pandas as pd
import pickle
from typing import Tuple, Dict
import os

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available. LSTM model will not work.")


class LSTMBinPredictor:
    """LSTM model for predicting bin fill levels using time series"""

    def __init__(self, sequence_length: int = 24, lstm_units: int = 64,
                 dropout_rate: float = 0.2, learning_rate: float = 0.001):
        """
        Initialize LSTM predictor

        Args:
            sequence_length: Number of time steps to look back
            lstm_units: Number of LSTM units
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTM model")

        self.sequence_length = sequence_length
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model = None
        self.history = None
        self.metrics = {}

    def create_sequences(self, data: np.ndarray, target: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training

        Args:
            data: Feature array
            target: Target array

        Returns:
            X sequences, y targets
        """
        X, y = [], []

        for i in range(len(data) - self.sequence_length):
            X.append(data[i:(i + self.sequence_length)])
            y.append(target[i + self.sequence_length])

        return np.array(X), np.array(y)

    def prepare_data(self, df: pd.DataFrame, target_col: str = 'fill_percentage',
                    test_size: float = 0.2) -> Tuple:
        """
        Prepare time series data for LSTM

        Args:
            df: DataFrame with time series data
            target_col: Target column name
            test_size: Proportion of data for testing

        Returns:
            X_train, y_train, X_test, y_test sequences
        """
        # Sort by bin_id and timestamp
        df = df.sort_values(['bin_id', 'timestamp'])

        # Extract features
        exclude_cols = ['bin_id', 'timestamp', target_col, 'bin_type', 'latitude', 'longitude']
        feature_cols = [col for col in df.columns if col not in exclude_cols]

        X_all = []
        y_all = []

        # Create sequences for each bin
        for bin_id in df['bin_id'].unique():
            bin_data = df[df['bin_id'] == bin_id]

            if len(bin_data) < self.sequence_length + 1:
                continue

            features = bin_data[feature_cols].values
            target = bin_data[target_col].values

            X_seq, y_seq = self.create_sequences(features, target)

            if len(X_seq) > 0:
                X_all.append(X_seq)
                y_all.append(y_seq)

        if len(X_all) == 0:
            raise ValueError("Not enough data to create sequences")

        X_all = np.vstack(X_all)
        y_all = np.concatenate(y_all)

        # Split into train and test
        split_idx = int(len(X_all) * (1 - test_size))

        X_train = X_all[:split_idx]
        y_train = y_all[:split_idx]
        X_test = X_all[split_idx:]
        y_test = y_all[split_idx:]

        print(f"✓ Prepared LSTM data:")
        print(f"  Training sequences: {len(X_train)}")
        print(f"  Testing sequences: {len(X_test)}")
        print(f"  Sequence length: {self.sequence_length}")
        print(f"  Features: {X_train.shape[2]}")

        return X_train, y_train, X_test, y_test

    def build_model(self, n_features: int):
        """
        Build LSTM model architecture

        Args:
            n_features: Number of input features
        """
        self.model = Sequential([
            LSTM(self.lstm_units, return_sequences=True,
                 input_shape=(self.sequence_length, n_features)),
            Dropout(self.dropout_rate),

            LSTM(self.lstm_units // 2, return_sequences=False),
            Dropout(self.dropout_rate),

            Dense(32, activation='relu'),
            Dropout(self.dropout_rate),

            Dense(1, activation='linear')
        ])

        optimizer = keras.optimizers.Adam(learning_rate=self.learning_rate)
        self.model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])

        print("✓ LSTM model built")
        print(self.model.summary())

    def train(self, X_train: np.ndarray, y_train: np.ndarray,
             X_val: np.ndarray = None, y_val: np.ndarray = None,
             epochs: int = 50, batch_size: int = 32) -> 'LSTMBinPredictor':
        """
        Train the LSTM model

        Args:
            X_train: Training sequences
            y_train: Training targets
            X_val: Validation sequences
            y_val: Validation targets
            epochs: Number of training epochs
            batch_size: Batch size

        Returns:
            Self for method chaining
        """
        if self.model is None:
            n_features = X_train.shape[2]
            self.build_model(n_features)

        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)
        ]

        print("Training LSTM model...")

        # Use validation split if validation data not provided
        if X_val is None or y_val is None:
            validation_data = None
            validation_split = 0.2
        else:
            validation_data = (X_val, y_val)
            validation_split = 0.0

        self.history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        print("✓ LSTM model trained")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Input sequences

        Returns:
            Predicted fill percentages
        """
        predictions = self.model.predict(X, verbose=0)
        predictions = np.clip(predictions.flatten(), 0, 100)
        return predictions

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance

        Args:
            X_test: Test sequences
            y_test: Test targets

        Returns:
            Dictionary of evaluation metrics
        """
        predictions = self.predict(X_test)

        mse = np.mean((y_test - predictions) ** 2)
        mae = np.mean(np.abs(y_test - predictions))
        rmse = np.sqrt(mse)
        r2 = 1 - (np.sum((y_test - predictions) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2))
        mape = np.mean(np.abs((y_test - predictions) / (y_test + 1e-10))) * 100

        self.metrics = {
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'mape': mape
        }

        print("\n📊 LSTM Model Performance:")
        print(f"  RMSE: {rmse:.2f}%")
        print(f"  MAE: {mae:.2f}%")
        print(f"  R² Score: {r2:.4f}")
        print(f"  MAPE: {mape:.2f}%")

        return self.metrics

    def save_model(self, filepath: str):
        """Save trained model to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Save model architecture and weights
        self.model.save(filepath)

        # Save configuration
        config = {
            'sequence_length': self.sequence_length,
            'lstm_units': self.lstm_units,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate,
            'metrics': self.metrics
        }

        config_path = filepath.replace('.h5', '_config.pkl').replace('.keras', '_config.pkl')
        with open(config_path, 'wb') as f:
            pickle.dump(config, f)

        print(f"✓ LSTM model saved to {filepath}")

    @staticmethod
    def load_model(filepath: str) -> 'LSTMBinPredictor':
        """Load trained model from file"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required to load LSTM model")

        # Load configuration
        config_path = filepath.replace('.h5', '_config.pkl').replace('.keras', '_config.pkl')
        with open(config_path, 'rb') as f:
            config = pickle.load(f)

        # Create instance
        predictor = LSTMBinPredictor(
            sequence_length=config['sequence_length'],
            lstm_units=config['lstm_units'],
            dropout_rate=config['dropout_rate'],
            learning_rate=config['learning_rate']
        )

        # Load model
        predictor.model = keras.models.load_model(filepath)
        predictor.metrics = config.get('metrics', {})

        print(f"✓ LSTM model loaded from {filepath}")
        return predictor


if __name__ == "__main__":
    # Example usage
    from src.data.preprocessing import BinDataPreprocessor
    from src.data.feature_engineering import BinFeatureEngineer

    # Load and prepare data
    preprocessor = BinDataPreprocessor()
    data = preprocessor.load_data('data/raw/smart-bins-argyle-square.csv')
    clean_data = preprocessor.clean_data()

    # Engineer features
    engineer = BinFeatureEngineer()
    featured_data = engineer.create_all_features(clean_data)

    # Create and train LSTM model
    lstm_predictor = LSTMBinPredictor(sequence_length=24, lstm_units=64)
    X_train, y_train, X_test, y_test = lstm_predictor.prepare_data(featured_data)

    lstm_predictor.train(X_train, y_train, epochs=50, batch_size=32)

    # Evaluate
    metrics = lstm_predictor.evaluate(X_test, y_test)

    # Save model
    lstm_predictor.save_model('models/lstm_model.keras')
