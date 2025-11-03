# 📊 Using Your Own Dataset - Complete Guide

This guide shows you how to use your own smart bin data with this project.

---

## 📋 Required Data Format

Your dataset must be a **CSV file** with the following columns:

### **Minimum Required Columns:**

| Column Name | Data Type | Description | Example |
|------------|-----------|-------------|---------|
| `bin_id` | String | Unique identifier for each bin | `BIN_001`, `TRASH_42` |
| `timestamp` | Datetime | When the measurement was taken | `2024-01-15 14:30:00` |
| `latitude` | Float | GPS latitude coordinate | `51.5294` |
| `longitude` | Float | GPS longitude coordinate | `-0.1194` |
| `fill_percentage` | Float | Current fill level (0-100%) | `75.5` |

### **Optional Columns:**

| Column Name | Data Type | Description | Example |
|------------|-----------|-------------|---------|
| `capacity_liters` | Integer | Bin capacity in liters | `240` |
| `temperature` | Float | Sensor temperature | `18.5` |
| `bin_type` | String | Type of waste | `General`, `Recycling`, `Organic` |

---

## 🚀 Quick Start - 3 Steps

### **Step 1: Prepare Your CSV File**

Your CSV should look like this:

```csv
bin_id,timestamp,latitude,longitude,fill_percentage,capacity_liters,temperature,bin_type
BIN_001,2024-01-01 08:00:00,51.5294,-0.1194,45.2,240,18.5,General
BIN_001,2024-01-01 09:00:00,51.5294,-0.1194,47.8,240,18.8,General
BIN_002,2024-01-01 08:00:00,51.5300,-0.1200,62.1,660,19.2,Recycling
BIN_002,2024-01-01 09:00:00,51.5300,-0.1200,63.5,660,19.5,Recycling
```

**Important Notes:**
- Each bin should have **multiple timestamps** (time series data)
- Minimum recommended: **7 days** of data for good predictions
- Ideal: **30+ days** of historical data
- Data frequency: Hourly readings work best, but any frequency is supported

### **Step 2: Place Your File**

Put your CSV file in the `data/raw/` directory:

```bash
# Option A: Name it exactly as expected (recommended)
mv your_data.csv data/raw/smart-bins-argyle-square.csv

# Option B: Keep your filename and specify path when running
# (see Step 3)
```

### **Step 3: Run the Project**

```bash
# Option A: If you named the file smart-bins-argyle-square.csv
python main.py

# Option B: Specify your custom filename
python main.py --data data/raw/your_data.csv

# With custom parameters
python main.py --data data/raw/your_data.csv --threshold 85 --vehicles 5
```

That's it! The project will automatically:
1. ✅ Load your data
2. ✅ Clean and validate it
3. ✅ Engineer features
4. ✅ Train prediction models
5. ✅ Optimize routes
6. ✅ Generate visualizations

---

## 📝 Detailed Instructions

### Data Format Requirements

#### 1. **Timestamp Format**

Accepted formats (will be auto-detected):
- `2024-01-15 14:30:00`
- `2024-01-15T14:30:00`
- `2024/01/15 14:30:00`
- `15-01-2024 14:30:00`
- Unix timestamp: `1705329000`

#### 2. **Fill Percentage**

- Must be between **0 and 100**
- Can be integer or float: `75`, `75.5`, `75.234`
- Values outside 0-100 will be filtered out

#### 3. **Coordinates**

- **Latitude**: -90 to 90 (decimal degrees)
- **Longitude**: -180 to 180 (decimal degrees)
- Example: `51.5294, -0.1194` (London)

#### 4. **Bin ID**

- Any string format works
- Must be consistent for each bin across all timestamps
- Examples: `BIN_001`, `TRASH-42`, `container_alpha`

---

## 🔧 Configuration for Your Data

### 1. Update Depot Location

Edit `config.yaml` or specify in code:

```yaml
routing:
  depot_location:
    latitude: 51.5294      # Change to your depot
    longitude: -0.1194     # Change to your depot
```

Or in code:

```python
from src.optimization.route_optimizer import WasteCollectionRouter

router = WasteCollectionRouter(
    depot_location=(YOUR_LAT, YOUR_LON),  # Your depot coordinates
    vehicle_capacity=10,
    num_vehicles=3
)
```

### 2. Adjust Route Parameters

```bash
# Set collection threshold (default: 80%)
python main.py --threshold 85

# Set number of vehicles
python main.py --vehicles 5

# Set vehicle capacity (bins per vehicle)
python main.py --capacity 15
```

### 3. Using the Dashboard

```bash
streamlit run app.py
```

Then configure your parameters in the sidebar!

---

## 💻 Python API for Custom Data

### Basic Usage:

```python
from src.data.preprocessing import BinDataPreprocessor
from src.data.feature_engineering import BinFeatureEngineer
from src.models.random_forest_model import BinFillPredictor

# Load YOUR data
preprocessor = BinDataPreprocessor()
data = preprocessor.load_data('data/raw/YOUR_FILE.csv')
clean_data = preprocessor.clean_data()

# Engineer features
engineer = BinFeatureEngineer()
featured_data = engineer.create_all_features(clean_data)

# Prepare for ML
X_train, y_train, X_test, y_test = engineer.prepare_ml_data(featured_data)

# Train model
predictor = BinFillPredictor(n_estimators=100)
predictor.train(X_train, y_train)
metrics = predictor.evaluate(X_test, y_test)

# Save model
predictor.save_model('models/my_custom_model.pkl')
```

### Making Predictions:

```python
# Get latest status
latest_status = preprocessor.get_latest_status()

# Make predictions
predictions = predictor.predict_future_fill(latest_status, hours_ahead=24)
print(predictions)
```

### Route Optimization:

```python
from src.optimization.route_optimizer import WasteCollectionRouter

# Initialize with YOUR depot location
router = WasteCollectionRouter(
    depot_location=(YOUR_LATITUDE, YOUR_LONGITUDE),
    vehicle_capacity=10,
    num_vehicles=3
)

# Get bins needing collection
bins_to_collect = router.get_bins_needing_collection(predictions, threshold=80)

# Optimize routes
result = router.optimize_routes(bins_to_collect)
print(f"Total distance: {result['total_distance_km']} km")
```

### Visualization:

```python
from src.visualization.map_viz import RouteMapVisualizer

visualizer = RouteMapVisualizer(center_location=(YOUR_LAT, YOUR_LON))

# Visualize routes
visualizer.visualize_routes(
    routes_result=result,
    bins_df=bins_to_collect,
    depot_location=(YOUR_LAT, YOUR_LON),
    save_path='my_routes.html'
)
```

---

## 📊 Example: Converting Your Data

### If your columns have different names:

```python
import pandas as pd

# Load your data
df = pd.read_csv('your_original_data.csv')

# Rename columns to match expected format
df = df.rename(columns={
    'sensor_id': 'bin_id',
    'recorded_at': 'timestamp',
    'lat': 'latitude',
    'lon': 'longitude',
    'fill_level': 'fill_percentage',
    'volume': 'capacity_liters'
})

# Save in correct format
df.to_csv('data/raw/smart-bins-argyle-square.csv', index=False)
```

### If fill_percentage is in different units:

```python
# If your data is 0-1 instead of 0-100
df['fill_percentage'] = df['fill_level'] * 100

# If your data is volume instead of percentage
df['fill_percentage'] = (df['current_volume'] / df['capacity']) * 100
```

---

## ✅ Data Validation Checklist

Before running, verify:

- [ ] CSV file is properly formatted (commas as separators)
- [ ] All required columns are present
- [ ] Timestamp column contains valid dates
- [ ] Fill percentage is between 0-100
- [ ] Coordinates are valid (latitude: -90 to 90, longitude: -180 to 180)
- [ ] Each bin has multiple time points (at least 24 hours of data)
- [ ] No completely empty columns
- [ ] File encoding is UTF-8 (if you have special characters)

---

## 🛠️ Troubleshooting

### Issue: "File not found"

**Solution:**
```bash
# Check file exists
ls data/raw/

# If missing, create directory
mkdir -p data/raw

# Copy your file
cp your_data.csv data/raw/smart-bins-argyle-square.csv
```

### Issue: "No bins need collection"

**Cause:** Your current fill levels are all below the threshold

**Solution:**
```bash
# Lower the threshold
python main.py --threshold 50
```

### Issue: "Not enough data to create sequences"

**Cause:** Not enough historical data per bin

**Solution:**
- Ensure each bin has at least 24 hours of data
- Check that bins have multiple timestamps

### Issue: "KeyError: column_name"

**Cause:** Missing required columns

**Solution:**
```python
# Check your columns
import pandas as pd
df = pd.read_csv('data/raw/your_file.csv')
print(df.columns.tolist())

# Rename as needed (see examples above)
```

### Issue: Poor prediction accuracy

**Solutions:**
- ✅ Add more historical data (30+ days recommended)
- ✅ Ensure regular time intervals
- ✅ Check for missing values
- ✅ Verify fill_percentage accuracy

---

## 📈 Best Practices

1. **Data Quality**
   - Clean, consistent timestamps
   - Regular measurement intervals (hourly recommended)
   - At least 30 days of history
   - Minimal missing values

2. **Bin Coverage**
   - At least 10 bins for meaningful routes
   - Geographic clustering for efficiency
   - Consistent bin types

3. **Model Retraining**
   - Retrain weekly with new data
   - Update when seasonal patterns change
   - Monitor prediction accuracy

4. **Route Optimization**
   - Set realistic vehicle capacities
   - Adjust thresholds based on bin types
   - Consider time windows if needed

---

## 🎯 Quick Test with Your Data

Run this to validate your data format:

```python
import pandas as pd
from src.data.preprocessing import BinDataPreprocessor

# Test loading
preprocessor = BinDataPreprocessor()
data = preprocessor.load_data('data/raw/YOUR_FILE.csv')

# Validate format
print(f"✓ Loaded {len(data)} records")
print(f"✓ Columns: {data.columns.tolist()}")
print(f"✓ Bins: {data['bin_id'].nunique()}")
print(f"✓ Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
print(f"✓ Fill range: {data['fill_percentage'].min():.1f}% to {data['fill_percentage'].max():.1f}%")

# Check for issues
required = ['bin_id', 'timestamp', 'latitude', 'longitude', 'fill_percentage']
missing = [col for col in required if col not in data.columns]
if missing:
    print(f"⚠ Missing columns: {missing}")
else:
    print("✓ All required columns present!")
```

---

## 📧 Need Help?

If you encounter issues with your data:

1. Check this guide's troubleshooting section
2. Validate your CSV format
3. Open an issue on GitHub with:
   - Sample of your data (first 5 rows)
   - Error messages
   - What you've tried

---

## 📚 Example Templates

### Minimal CSV Template:

```csv
bin_id,timestamp,latitude,longitude,fill_percentage
BIN_001,2024-01-01 00:00:00,51.5294,-0.1194,10.5
BIN_001,2024-01-01 01:00:00,51.5294,-0.1194,12.3
BIN_001,2024-01-01 02:00:00,51.5294,-0.1194,14.1
```

### Full CSV Template:

```csv
bin_id,timestamp,latitude,longitude,fill_percentage,capacity_liters,temperature,bin_type
BIN_001,2024-01-01 00:00:00,51.5294,-0.1194,10.5,240,18.5,General
BIN_001,2024-01-01 01:00:00,51.5294,-0.1194,12.3,240,18.6,General
BIN_002,2024-01-01 00:00:00,51.5300,-0.1200,45.2,660,19.0,Recycling
BIN_002,2024-01-01 01:00:00,51.5300,-0.1200,46.8,660,19.1,Recycling
```

---

**You're all set! 🚀**

Place your CSV file and run `python main.py --data data/raw/your_file.csv`
