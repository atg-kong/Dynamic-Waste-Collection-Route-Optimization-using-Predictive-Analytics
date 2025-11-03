"""
Random Forest model for bin fill level prediction
"""

import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Tuple, Dict
import os


class BinFillPredictor:
    """Random Forest model for predicting bin fill levels"""

    def __init__(self, n_estimators: int = 100, max_depth: int = 20,
                 min_samples_split: int = 5, random_state: int = 42):
        """
        Initialize Random Forest predictor

        Args:
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of trees
            min_samples_split: Minimum samples required to split a node
            random_state: Random seed for reproducibility
        """
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            random_state=random_state,
            n_jobs=-1
        )
        self.feature_importance = None
        self.feature_names = None
        self.metrics = {}

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> 'BinFillPredictor':
        """
        Train the Random Forest model

        Args:
            X_train: Training features
            y_train: Training target

        Returns:
            Self for method chaining
        """
        print("Training Random Forest model...")
        self.feature_names = X_train.columns.tolist()

        self.model.fit(X_train, y_train)

        # Calculate feature importance
        self.feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        print(f"✓ Model trained with {len(self.feature_names)} features")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Features for prediction

        Returns:
            Predicted fill percentages
        """
        predictions = self.model.predict(X)
        # Ensure predictions are within valid range
        predictions = np.clip(predictions, 0, 100)
        return predictions

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """
        Evaluate model performance

        Args:
            X_test: Test features
            y_test: Test target

        Returns:
            Dictionary of evaluation metrics
        """
        predictions = self.predict(X_test)

        self.metrics = {
            'rmse': np.sqrt(mean_squared_error(y_test, predictions)),
            'mae': mean_absolute_error(y_test, predictions),
            'r2': r2_score(y_test, predictions),
            'mape': np.mean(np.abs((y_test - predictions) / (y_test + 1e-10))) * 100
        }

        print("\n📊 Model Performance:")
        print(f"  RMSE: {self.metrics['rmse']:.2f}%")
        print(f"  MAE: {self.metrics['mae']:.2f}%")
        print(f"  R² Score: {self.metrics['r2']:.4f}")
        print(f"  MAPE: {self.metrics['mape']:.2f}%")

        return self.metrics

    def predict_future_fill(self, current_data: pd.DataFrame,
                           hours_ahead: int = 24) -> pd.DataFrame:
        """
        Predict future fill levels for bins

        Args:
            current_data: Current bin status with features
            hours_ahead: Number of hours to predict ahead

        Returns:
            DataFrame with predictions
        """
        predictions = []

        for bin_id in current_data['bin_id'].unique():
            bin_data = current_data[current_data['bin_id'] == bin_id].copy()

            if len(bin_data) == 0:
                continue

            latest = bin_data.iloc[-1]

            # Extract features for prediction
            feature_cols = [col for col in bin_data.columns
                          if col not in ['bin_id', 'timestamp', 'fill_percentage',
                                       'latitude', 'longitude', 'bin_type']]

            if len(feature_cols) == 0:
                continue

            X = bin_data[feature_cols].iloc[-1:].values

            # Predict
            predicted_fill = self.model.predict(X)[0]
            predicted_fill = np.clip(predicted_fill, 0, 100)

            predictions.append({
                'bin_id': bin_id,
                'current_fill': latest['fill_percentage'],
                'predicted_fill': round(predicted_fill, 2),
                'latitude': latest['latitude'],
                'longitude': latest['longitude'],
                'hours_ahead': hours_ahead,
                'needs_collection': predicted_fill >= 80
            })

        return pd.DataFrame(predictions)

    def plot_feature_importance(self, top_n: int = 15, save_path: str = None):
        """
        Plot feature importance

        Args:
            top_n: Number of top features to display
            save_path: Path to save the plot
        """
        if self.feature_importance is None:
            print("Model not trained yet.")
            return

        plt.figure(figsize=(10, 6))
        top_features = self.feature_importance.head(top_n)

        sns.barplot(data=top_features, x='importance', y='feature', palette='viridis')
        plt.title(f'Top {top_n} Feature Importances')
        plt.xlabel('Importance')
        plt.ylabel('Feature')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ Feature importance plot saved to {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_predictions(self, y_true: np.ndarray, y_pred: np.ndarray, save_path: str = None):
        """
        Plot actual vs predicted values

        Args:
            y_true: True values
            y_pred: Predicted values
            save_path: Path to save the plot
        """
        plt.figure(figsize=(10, 6))

        plt.scatter(y_true, y_pred, alpha=0.5, s=10)
        plt.plot([0, 100], [0, 100], 'r--', lw=2, label='Perfect Prediction')

        plt.xlabel('Actual Fill Percentage')
        plt.ylabel('Predicted Fill Percentage')
        plt.title('Actual vs Predicted Fill Levels')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✓ Predictions plot saved to {save_path}")
        else:
            plt.show()

        plt.close()

    def save_model(self, filepath: str):
        """Save trained model to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"✓ Model saved to {filepath}")

    @staticmethod
    def load_model(filepath: str) -> 'BinFillPredictor':
        """Load trained model from file"""
        with open(filepath, 'rb') as f:
            model = pickle.load(f)
        print(f"✓ Model loaded from {filepath}")
        return model


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

    # Prepare ML data
    X_train, y_train, X_test, y_test = engineer.prepare_ml_data(featured_data)

    # Train model
    predictor = BinFillPredictor(n_estimators=100, max_depth=20)
    predictor.train(X_train, y_train)

    # Evaluate
    metrics = predictor.evaluate(X_test, y_test)

    # Plot feature importance
    predictor.plot_feature_importance(save_path='models/feature_importance.png')

    # Plot predictions
    predictions = predictor.predict(X_test)
    predictor.plot_predictions(y_test.values, predictions, save_path='models/predictions.png')

    # Save model
    predictor.save_model('models/random_forest_model.pkl')
