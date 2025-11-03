"""
Feature engineering for bin fill level prediction
"""

import pandas as pd
import numpy as np
from typing import List, Tuple
from sklearn.preprocessing import StandardScaler, LabelEncoder


class BinFeatureEngineer:
    """Feature engineering for smart bin data"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}

    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create time-based features from timestamp

        Args:
            df: DataFrame with timestamp column

        Returns:
            DataFrame with additional time features
        """
        df = df.copy()

        if 'timestamp' not in df.columns:
            raise ValueError("DataFrame must have 'timestamp' column")

        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

        # Business hours flag
        df['is_business_hours'] = ((df['hour'] >= 8) & (df['hour'] <= 18)).astype(int)

        # Cyclical encoding for time features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

        print(f"✓ Created time-based features")
        return df

    def create_lag_features(self, df: pd.DataFrame, target_col: str = 'fill_percentage',
                           lags: List[int] = [1, 2, 3, 6, 12, 24]) -> pd.DataFrame:
        """
        Create lag features for time series prediction

        Args:
            df: DataFrame sorted by bin_id and timestamp
            target_col: Target column to create lags for
            lags: List of lag periods

        Returns:
            DataFrame with lag features
        """
        df = df.copy()
        df = df.sort_values(['bin_id', 'timestamp'])

        for lag in lags:
            df[f'{target_col}_lag_{lag}'] = df.groupby('bin_id')[target_col].shift(lag)

        # Fill NaN values with forward fill and then backward fill
        lag_cols = [f'{target_col}_lag_{lag}' for lag in lags]
        df[lag_cols] = df.groupby('bin_id')[lag_cols].fillna(method='ffill').fillna(method='bfill')

        print(f"✓ Created {len(lags)} lag features")
        return df

    def create_rolling_features(self, df: pd.DataFrame, target_col: str = 'fill_percentage',
                               windows: List[int] = [3, 6, 12, 24]) -> pd.DataFrame:
        """
        Create rolling statistics features

        Args:
            df: DataFrame sorted by bin_id and timestamp
            target_col: Target column for rolling statistics
            windows: List of window sizes

        Returns:
            DataFrame with rolling features
        """
        df = df.copy()
        df = df.sort_values(['bin_id', 'timestamp'])

        for window in windows:
            # Rolling mean
            df[f'{target_col}_rolling_mean_{window}'] = (
                df.groupby('bin_id')[target_col]
                .rolling(window=window, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )

            # Rolling std
            df[f'{target_col}_rolling_std_{window}'] = (
                df.groupby('bin_id')[target_col]
                .rolling(window=window, min_periods=1)
                .std()
                .reset_index(level=0, drop=True)
            )

            # Rolling max
            df[f'{target_col}_rolling_max_{window}'] = (
                df.groupby('bin_id')[target_col]
                .rolling(window=window, min_periods=1)
                .max()
                .reset_index(level=0, drop=True)
            )

        # Fill any remaining NaN with 0
        rolling_cols = [col for col in df.columns if 'rolling' in col]
        df[rolling_cols] = df[rolling_cols].fillna(0)

        print(f"✓ Created rolling features for {len(windows)} windows")
        return df

    def create_rate_features(self, df: pd.DataFrame, target_col: str = 'fill_percentage') -> pd.DataFrame:
        """
        Create fill rate change features

        Args:
            df: DataFrame sorted by bin_id and timestamp
            target_col: Target column for rate calculation

        Returns:
            DataFrame with rate features
        """
        df = df.copy()
        df = df.sort_values(['bin_id', 'timestamp'])

        # Calculate rate of change
        df['fill_rate'] = df.groupby('bin_id')[target_col].diff()

        # Rate of change over different periods
        df['fill_rate_3h'] = df.groupby('bin_id')[target_col].diff(3)
        df['fill_rate_6h'] = df.groupby('bin_id')[target_col].diff(6)

        # Fill NaN values
        rate_cols = [col for col in df.columns if 'fill_rate' in col]
        df[rate_cols] = df[rate_cols].fillna(0)

        print(f"✓ Created rate-of-change features")
        return df

    def encode_categorical_features(self, df: pd.DataFrame,
                                    cat_columns: List[str] = None) -> pd.DataFrame:
        """
        Encode categorical features

        Args:
            df: DataFrame with categorical columns
            cat_columns: List of categorical columns to encode

        Returns:
            DataFrame with encoded features
        """
        df = df.copy()

        if cat_columns is None:
            cat_columns = ['bin_type']

        for col in cat_columns:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col].astype(str))

        print(f"✓ Encoded {len(cat_columns)} categorical features")
        return df

    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create all features at once

        Args:
            df: Raw DataFrame

        Returns:
            DataFrame with all engineered features
        """
        print("Creating all features...")

        # Time features
        df = self.create_time_features(df)

        # Lag features
        df = self.create_lag_features(df)

        # Rolling features
        df = self.create_rolling_features(df)

        # Rate features
        df = self.create_rate_features(df)

        # Encode categorical features
        if 'bin_type' in df.columns:
            df = self.encode_categorical_features(df)

        print(f"✓ Feature engineering complete. Total features: {len(df.columns)}")
        return df

    def prepare_ml_data(self, df: pd.DataFrame,
                       target_col: str = 'fill_percentage',
                       test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """
        Prepare data for machine learning

        Args:
            df: DataFrame with all features
            target_col: Target column name
            test_size: Proportion of data for testing

        Returns:
            X_train, y_train, X_test, y_test
        """
        # Define feature columns (exclude non-feature columns)
        exclude_cols = ['bin_id', 'timestamp', target_col, 'bin_type', 'latitude', 'longitude']
        feature_cols = [col for col in df.columns if col not in exclude_cols]

        # Split by time (later data for testing)
        df = df.sort_values('timestamp')
        split_idx = int(len(df) * (1 - test_size))

        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]

        X_train = train_df[feature_cols]
        y_train = train_df[target_col]
        X_test = test_df[feature_cols]
        y_test = test_df[target_col]

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        X_train = pd.DataFrame(X_train_scaled, columns=feature_cols, index=X_train.index)
        X_test = pd.DataFrame(X_test_scaled, columns=feature_cols, index=X_test.index)

        print(f"✓ Prepared ML data:")
        print(f"  Training samples: {len(X_train)}")
        print(f"  Testing samples: {len(X_test)}")
        print(f"  Features: {len(feature_cols)}")

        return X_train, y_train, X_test, y_test


if __name__ == "__main__":
    # Example usage
    from preprocessing import BinDataPreprocessor

    preprocessor = BinDataPreprocessor()
    data = preprocessor.load_data('data/raw/smart-bins-argyle-square.csv')
    clean_data = preprocessor.clean_data()

    engineer = BinFeatureEngineer()
    featured_data = engineer.create_all_features(clean_data)

    print("\nFeatured data sample:")
    print(featured_data.head())
    print("\nFeature columns:")
    print(featured_data.columns.tolist())
