"""
Data preprocessing module for smart bin data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class BinDataPreprocessor:
    """Preprocessor for smart bin sensor data"""

    def __init__(self):
        self.data = None
        self.feature_columns = []

    def load_data(self, filepath: str) -> pd.DataFrame:
        """
        Load smart bin data from CSV file

        Args:
            filepath: Path to the CSV file

        Returns:
            DataFrame with loaded data
        """
        try:
            self.data = pd.read_csv(filepath)
            print(f"✓ Loaded {len(self.data)} records from {filepath}")
            return self.data
        except FileNotFoundError:
            print(f"Warning: {filepath} not found. Generating sample data...")
            return self.generate_sample_data()

    def generate_sample_data(self, n_bins: int = 20, days: int = 30) -> pd.DataFrame:
        """
        Generate sample smart bin data for demonstration

        Args:
            n_bins: Number of bins to simulate
            days: Number of days of historical data

        Returns:
            DataFrame with sample data
        """
        np.random.seed(42)

        # Argyle Square, London approximate coordinates
        base_lat, base_lon = 51.5294, -0.1194

        data = []
        start_date = datetime.now() - timedelta(days=days)

        for bin_id in range(1, n_bins + 1):
            # Random location near Argyle Square
            lat = base_lat + np.random.uniform(-0.005, 0.005)
            lon = base_lon + np.random.uniform(-0.005, 0.005)

            # Bin capacity in liters
            capacity = np.random.choice([120, 240, 660, 1100])

            # Generate time series data
            current_fill = np.random.uniform(0, 30)  # Start with low fill

            for hour in range(days * 24):
                timestamp = start_date + timedelta(hours=hour)

                # Simulate fill behavior
                # Higher fill rate during business hours and weekdays
                hour_of_day = timestamp.hour
                day_of_week = timestamp.weekday()

                # Fill rate varies by time and day
                if 8 <= hour_of_day <= 20 and day_of_week < 5:
                    fill_increase = np.random.uniform(2, 8)
                elif day_of_week >= 5:
                    fill_increase = np.random.uniform(1, 4)
                else:
                    fill_increase = np.random.uniform(0.5, 2)

                current_fill += fill_increase

                # Add some noise
                current_fill += np.random.normal(0, 1)

                # Reset if collected (when fill > 80%)
                if current_fill > 80:
                    current_fill = np.random.uniform(0, 15)

                # Ensure bounds
                current_fill = np.clip(current_fill, 0, 100)

                data.append({
                    'bin_id': f'BIN_{bin_id:03d}',
                    'timestamp': timestamp,
                    'latitude': lat,
                    'longitude': lon,
                    'fill_percentage': round(current_fill, 2),
                    'capacity_liters': capacity,
                    'temperature': np.random.uniform(15, 25),
                    'bin_type': np.random.choice(['General', 'Recycling', 'Organic'])
                })

        self.data = pd.DataFrame(data)
        print(f"✓ Generated {len(self.data)} sample records for {n_bins} bins")
        return self.data

    def clean_data(self) -> pd.DataFrame:
        """
        Clean and prepare data for modeling

        Returns:
            Cleaned DataFrame
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")

        df = self.data.copy()

        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Remove duplicates
        initial_rows = len(df)
        df = df.drop_duplicates()
        if len(df) < initial_rows:
            print(f"✓ Removed {initial_rows - len(df)} duplicate records")

        # Handle missing values
        missing_count = df.isnull().sum().sum()
        if missing_count > 0:
            print(f"✓ Found {missing_count} missing values")
            # Forward fill for time series data
            df = df.sort_values(['bin_id', 'timestamp'])
            df = df.fillna(method='ffill').fillna(method='bfill')

        # Remove outliers in fill_percentage
        df = df[(df['fill_percentage'] >= 0) & (df['fill_percentage'] <= 100)]

        # Sort by bin_id and timestamp
        df = df.sort_values(['bin_id', 'timestamp']).reset_index(drop=True)

        self.data = df
        print(f"✓ Cleaned data: {len(df)} records")
        return df

    def get_latest_status(self) -> pd.DataFrame:
        """
        Get the latest status for each bin

        Returns:
            DataFrame with latest status per bin
        """
        if self.data is None:
            raise ValueError("No data loaded.")

        latest = self.data.sort_values('timestamp').groupby('bin_id').tail(1)
        return latest.reset_index(drop=True)

    def save_processed_data(self, filepath: str):
        """Save processed data to CSV"""
        if self.data is None:
            raise ValueError("No data to save.")

        self.data.to_csv(filepath, index=False)
        print(f"✓ Saved processed data to {filepath}")


if __name__ == "__main__":
    # Example usage
    preprocessor = BinDataPreprocessor()

    # Try to load real data, fall back to sample data
    data = preprocessor.load_data('data/raw/smart-bins-argyle-square.csv')

    # Clean the data
    clean_data = preprocessor.clean_data()

    # Show summary
    print("\nData Summary:")
    print(f"Total records: {len(clean_data)}")
    print(f"Number of bins: {clean_data['bin_id'].nunique()}")
    print(f"Date range: {clean_data['timestamp'].min()} to {clean_data['timestamp'].max()}")
    print(f"\nFill percentage statistics:")
    print(clean_data['fill_percentage'].describe())

    # Save processed data
    preprocessor.save_processed_data('data/processed/cleaned_bin_data.csv')
