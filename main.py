"""
Main execution script for Dynamic Waste Collection Route Optimization
"""

import os
import sys
import argparse
import warnings
warnings.filterwarnings('ignore')

from src.data.preprocessing import BinDataPreprocessor
from src.data.feature_engineering import BinFeatureEngineer
from src.models.random_forest_model import BinFillPredictor
from src.optimization.route_optimizer import WasteCollectionRouter
from src.visualization.map_viz import RouteMapVisualizer


def setup_directories():
    """Create necessary directories"""
    directories = [
        'data/raw',
        'data/processed',
        'models',
        'output/maps',
        'output/plots'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def train_model(data_path='data/raw/smart-bins-argyle-square.csv'):
    """Train the prediction model"""
    print("\n" + "="*60)
    print("STEP 1: DATA PREPROCESSING & FEATURE ENGINEERING")
    print("="*60)

    # Load and preprocess data
    preprocessor = BinDataPreprocessor()
    data = preprocessor.load_data(data_path)
    clean_data = preprocessor.clean_data()

    # Save processed data
    preprocessor.save_processed_data('data/processed/cleaned_bin_data.csv')

    # Feature engineering
    engineer = BinFeatureEngineer()
    featured_data = engineer.create_all_features(clean_data)

    # Prepare ML data
    X_train, y_train, X_test, y_test = engineer.prepare_ml_data(featured_data)

    print("\n" + "="*60)
    print("STEP 2: MODEL TRAINING")
    print("="*60)

    # Train Random Forest model
    predictor = BinFillPredictor(n_estimators=100, max_depth=20)
    predictor.train(X_train, y_train)

    # Evaluate
    metrics = predictor.evaluate(X_test, y_test)

    # Plot results
    print("\nGenerating visualizations...")
    predictor.plot_feature_importance(save_path='output/plots/feature_importance.png')

    predictions = predictor.predict(X_test)
    predictor.plot_predictions(y_test.values, predictions, save_path='output/plots/predictions.png')

    # Save model
    predictor.save_model('models/random_forest_model.pkl')

    return preprocessor, engineer, predictor, clean_data


def predict_and_optimize(preprocessor, engineer, predictor, clean_data,
                        threshold=80.0, depot_location=(51.5294, -0.1194),
                        num_vehicles=3, vehicle_capacity=10):
    """Make predictions and optimize routes"""
    print("\n" + "="*60)
    print("STEP 3: PREDICTION & ROUTE OPTIMIZATION")
    print("="*60)

    # Get latest bin status
    latest_status = preprocessor.get_latest_status()

    # Prepare features for prediction
    latest_featured = engineer.create_all_features(
        preprocessor.data[preprocessor.data['bin_id'].isin(latest_status['bin_id'])]
    )
    latest_featured = latest_featured.groupby('bin_id').tail(1)

    # Extract features
    exclude_cols = ['bin_id', 'timestamp', 'fill_percentage', 'bin_type',
                   'latitude', 'longitude']
    feature_cols = [col for col in latest_featured.columns if col not in exclude_cols]

    if len(feature_cols) > 0:
        X_predict = latest_featured[feature_cols]

        # Standardize features using the same scaler
        X_predict_scaled = engineer.scaler.transform(X_predict)

        # Make predictions
        predictions = predictor.predict(X_predict_scaled)

        # Add predictions to latest status
        latest_status['predicted_fill'] = predictions

        print(f"\n✓ Predictions completed for {len(latest_status)} bins")
        print(f"  Average predicted fill: {predictions.mean():.2f}%")
        print(f"  Bins predicted ≥{threshold}%: {(predictions >= threshold).sum()}")

        # Initialize router
        router = WasteCollectionRouter(
            depot_location=depot_location,
            vehicle_capacity=vehicle_capacity,
            num_vehicles=num_vehicles
        )

        # Get bins needing collection
        bins_to_collect = router.get_bins_needing_collection(latest_status, threshold=threshold)

        if len(bins_to_collect) > 0:
            # Optimize routes
            result = router.optimize_routes(bins_to_collect, time_limit_seconds=30)

            print("\n" + "="*60)
            print("STEP 4: VISUALIZATION")
            print("="*60)

            # Create visualizations
            visualizer = RouteMapVisualizer(center_location=depot_location)

            # Visualize optimized routes
            visualizer.visualize_routes(
                result,
                latest_status,
                depot_location,
                save_path='output/maps/optimized_routes.html'
            )

            # Visualize bin status
            visualizer.visualize_bin_status(
                latest_status,
                save_path='output/maps/bin_status.html'
            )

            print("\n" + "="*60)
            print("OPTIMIZATION COMPLETE!")
            print("="*60)
            print(f"\n📊 Summary:")
            print(f"  • Total bins monitored: {len(latest_status)}")
            print(f"  • Bins needing collection: {result['total_bins_collected']}")
            print(f"  • Vehicles deployed: {result['num_vehicles_used']}")
            print(f"  • Total route distance: {result['total_distance_km']} km")
            print(f"\n📁 Output files:")
            print(f"  • Maps: output/maps/")
            print(f"  • Plots: output/plots/")
            print(f"  • Model: models/random_forest_model.pkl")

            return result
        else:
            print(f"\n✓ No bins need collection (threshold: {threshold}%)")
            return None


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Dynamic Waste Collection Route Optimization using Predictive Analytics'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='data/raw/smart-bins-argyle-square.csv',
        help='Path to input CSV file'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=80.0,
        help='Fill percentage threshold for collection (default: 80)'
    )
    parser.add_argument(
        '--vehicles',
        type=int,
        default=3,
        help='Number of collection vehicles (default: 3)'
    )
    parser.add_argument(
        '--capacity',
        type=int,
        default=10,
        help='Vehicle capacity in bins (default: 10)'
    )
    parser.add_argument(
        '--skip-training',
        action='store_true',
        help='Skip training and use existing model'
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("DYNAMIC WASTE COLLECTION ROUTE OPTIMIZATION")
    print("Using Predictive Analytics")
    print("="*60)

    # Setup
    setup_directories()

    # Train or load model
    if args.skip_training and os.path.exists('models/random_forest_model.pkl'):
        print("\nLoading existing model...")
        predictor = BinFillPredictor.load_model('models/random_forest_model.pkl')

        preprocessor = BinDataPreprocessor()
        data = preprocessor.load_data(args.data)
        clean_data = preprocessor.clean_data()

        engineer = BinFeatureEngineer()
        engineer.create_all_features(clean_data)
    else:
        preprocessor, engineer, predictor, clean_data = train_model(args.data)

    # Predict and optimize
    result = predict_and_optimize(
        preprocessor,
        engineer,
        predictor,
        clean_data,
        threshold=args.threshold,
        num_vehicles=args.vehicles,
        vehicle_capacity=args.capacity
    )

    print("\n✓ All done! Check the output/ directory for results.")
    print("💡 To view the dashboard, run: streamlit run app.py\n")


if __name__ == "__main__":
    main()
