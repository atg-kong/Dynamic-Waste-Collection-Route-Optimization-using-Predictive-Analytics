"""
Quick fix script to check your CSV column names
"""
import pandas as pd

print("Checking your CSV file...")
print("="*70)

try:
    # Try to read the CSV
    df = pd.read_csv('data/raw/smart-bins-argyle-square.csv')

    print(f"\n✓ File loaded successfully!")
    print(f"Total rows: {len(df)}")
    print(f"\nColumn names in YOUR CSV file:")
    print("-"*70)
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")

    print("\n" + "="*70)
    print("REQUIRED column names:")
    print("-"*70)
    print("  1. bin_id")
    print("  2. timestamp")
    print("  3. latitude")
    print("  4. longitude")
    print("  5. fill_percentage")

    print("\n" + "="*70)
    print("\nFirst 3 rows of your data:")
    print("-"*70)
    print(df.head(3))

    # Check which columns are missing
    required = ['bin_id', 'timestamp', 'latitude', 'longitude', 'fill_percentage']
    missing = [col for col in required if col not in df.columns]

    if missing:
        print("\n⚠️  MISSING COLUMNS:")
        for col in missing:
            print(f"   - {col}")
        print("\nYou need to either:")
        print("  1. Rename your CSV columns to match the required names")
        print("  2. Or tell me what your columns are called so I can update the code")
    else:
        print("\n✅ All required columns are present!")

except FileNotFoundError:
    print("❌ ERROR: File not found at data/raw/smart-bins-argyle-square.csv")
    print("\nPlease make sure your CSV file is in the correct location.")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print("\n" + "="*70)
