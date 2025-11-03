"""
Data Validation Script - Check if your custom data is compatible
Run this before using your own dataset with the project
"""

import pandas as pd
import sys
from datetime import datetime

def validate_data(filepath: str):
    """
    Validate custom dataset for compatibility

    Args:
        filepath: Path to your CSV file
    """
    print("="*60)
    print("DATA VALIDATION TOOL")
    print("="*60)
    print(f"\nValidating: {filepath}\n")

    # Required columns
    required_cols = ['bin_id', 'timestamp', 'latitude', 'longitude', 'fill_percentage']
    optional_cols = ['capacity_liters', 'temperature', 'bin_type']

    issues = []
    warnings = []

    try:
        # Load data
        print("📂 Loading data...")
        df = pd.read_csv(filepath)
        print(f"   ✓ Successfully loaded {len(df)} records")

        # Check required columns
        print("\n📋 Checking required columns...")
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")
            print(f"   ✗ Missing: {missing_cols}")
            print(f"   Found columns: {df.columns.tolist()}")
        else:
            print(f"   ✓ All required columns present")

        # Check optional columns
        print("\n📋 Checking optional columns...")
        present_optional = [col for col in optional_cols if col in df.columns]
        missing_optional = [col for col in optional_cols if col not in df.columns]

        if present_optional:
            print(f"   ✓ Optional columns found: {present_optional}")
        if missing_optional:
            print(f"   ℹ Optional columns missing: {missing_optional} (not required)")

        if not missing_cols:  # Only continue validation if required columns exist

            # Validate timestamps
            print("\n📅 Validating timestamps...")
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                print(f"   ✓ Timestamps are valid")
                print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

                # Check time span
                time_span = (df['timestamp'].max() - df['timestamp'].min()).days
                if time_span < 7:
                    warnings.append(f"Only {time_span} days of data (recommended: 30+ days)")
                    print(f"   ⚠ Warning: Only {time_span} days of data")
                else:
                    print(f"   ✓ Good time span: {time_span} days")

            except Exception as e:
                issues.append(f"Invalid timestamp format: {e}")
                print(f"   ✗ Timestamp validation failed: {e}")

            # Validate bin_id
            print("\n🗑️  Validating bin IDs...")
            n_bins = df['bin_id'].nunique()
            print(f"   ✓ Found {n_bins} unique bins")

            if n_bins < 5:
                warnings.append(f"Only {n_bins} bins (recommended: 10+ for meaningful routes)")
                print(f"   ⚠ Warning: Few bins detected")

            # Check records per bin
            records_per_bin = df.groupby('bin_id').size()
            min_records = records_per_bin.min()
            avg_records = records_per_bin.mean()

            print(f"   Records per bin: min={min_records}, avg={avg_records:.1f}")

            if min_records < 24:
                warnings.append(f"Some bins have < 24 records (min: {min_records})")
                print(f"   ⚠ Warning: Some bins have insufficient data")

            # Validate fill_percentage
            print("\n📊 Validating fill percentage...")
            fill_min = df['fill_percentage'].min()
            fill_max = df['fill_percentage'].max()
            fill_mean = df['fill_percentage'].mean()

            print(f"   Range: {fill_min:.1f}% to {fill_max:.1f}%")
            print(f"   Average: {fill_mean:.1f}%")

            if fill_min < 0 or fill_max > 100:
                issues.append(f"Fill percentage out of range: {fill_min:.1f}% to {fill_max:.1f}%")
                print(f"   ✗ Values outside 0-100% range")
            else:
                print(f"   ✓ Values within valid range")

            # Check for negative or null values
            null_fill = df['fill_percentage'].isnull().sum()
            if null_fill > 0:
                warnings.append(f"{null_fill} missing fill_percentage values")
                print(f"   ⚠ {null_fill} missing values (will be handled)")

            # Validate coordinates
            print("\n🗺️  Validating coordinates...")
            lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
            lon_min, lon_max = df['longitude'].min(), df['longitude'].max()

            print(f"   Latitude range: {lat_min:.4f} to {lat_max:.4f}")
            print(f"   Longitude range: {lon_min:.4f} to {lon_max:.4f}")

            if not (-90 <= lat_min <= 90) or not (-90 <= lat_max <= 90):
                issues.append(f"Invalid latitude values: {lat_min} to {lat_max}")
                print(f"   ✗ Latitude out of range (-90 to 90)")
            else:
                print(f"   ✓ Valid latitude range")

            if not (-180 <= lon_min <= 180) or not (-180 <= lon_max <= 180):
                issues.append(f"Invalid longitude values: {lon_min} to {lon_max}")
                print(f"   ✗ Longitude out of range (-180 to 180)")
            else:
                print(f"   ✓ Valid longitude range")

            # Check for duplicates
            print("\n🔍 Checking data quality...")
            n_duplicates = df.duplicated().sum()
            if n_duplicates > 0:
                warnings.append(f"{n_duplicates} duplicate records")
                print(f"   ⚠ {n_duplicates} duplicate records (will be removed)")
            else:
                print(f"   ✓ No duplicate records")

            # Check missing values
            total_missing = df.isnull().sum().sum()
            if total_missing > 0:
                print(f"   ⚠ {total_missing} total missing values")
                for col in df.columns:
                    missing = df[col].isnull().sum()
                    if missing > 0:
                        print(f"      - {col}: {missing} missing")
            else:
                print(f"   ✓ No missing values")

            # Sample data preview
            print("\n📋 Sample data (first 3 rows):")
            print(df.head(3).to_string(index=False))

        # Summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)

        if not issues:
            print("\n✅ VALIDATION PASSED!")
            print("\nYour data is compatible with the project!")
            print("\nNext steps:")
            print("  1. Place your file in: data/raw/smart-bins-argyle-square.csv")
            print("  2. Or run: python main.py --data", filepath)

            if warnings:
                print("\n⚠️  WARNINGS (non-critical):")
                for i, warning in enumerate(warnings, 1):
                    print(f"   {i}. {warning}")
                print("\nThese won't prevent the project from running,")
                print("but more/better data will improve results.")
        else:
            print("\n❌ VALIDATION FAILED!")
            print("\nIssues found:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")

            if warnings:
                print("\nWarnings:")
                for i, warning in enumerate(warnings, 1):
                    print(f"   {i}. {warning}")

            print("\nPlease fix these issues before using your data.")
            print("See CUSTOM_DATA_GUIDE.md for help.")

            return False

        return True

    except FileNotFoundError:
        print(f"   ✗ File not found: {filepath}")
        print("\nMake sure the file path is correct.")
        return False

    except Exception as e:
        print(f"   ✗ Error reading file: {e}")
        print("\nMake sure the file is a valid CSV.")
        return False


def show_usage():
    """Show usage instructions"""
    print("""
Usage:
    python validate_data.py <path_to_your_csv>

Example:
    python validate_data.py data/raw/my_bin_data.csv
    python validate_data.py /path/to/your/data.csv

This tool checks if your data is compatible with the project.
    """)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Error: No file path provided\n")
        show_usage()
        sys.exit(1)

    filepath = sys.argv[1]

    success = validate_data(filepath)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
