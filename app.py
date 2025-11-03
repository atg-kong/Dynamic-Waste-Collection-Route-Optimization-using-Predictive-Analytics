"""
Streamlit Dashboard for Waste Collection Route Optimization
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys

# Add src to path
sys.path.append('src')

from src.data.preprocessing import BinDataPreprocessor
from src.data.feature_engineering import BinFeatureEngineer
from src.models.random_forest_model import BinFillPredictor
from src.optimization.route_optimizer import WasteCollectionRouter
from src.visualization.map_viz import RouteMapVisualizer

# Page configuration
st.set_page_config(
    page_title="Smart Waste Collection",
    page_icon="🗑️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stAlert {
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_and_prepare_data():
    """Load and prepare data with caching"""
    preprocessor = BinDataPreprocessor()
    data = preprocessor.load_data('data/raw/smart-bins-argyle-square.csv')
    clean_data = preprocessor.clean_data()

    engineer = BinFeatureEngineer()
    featured_data = engineer.create_all_features(clean_data)

    return preprocessor, engineer, featured_data


@st.cache_resource
def load_model():
    """Load trained model with caching"""
    model_path = 'models/random_forest_model.pkl'

    if os.path.exists(model_path):
        predictor = BinFillPredictor.load_model(model_path)
        st.success("✓ Loaded pre-trained model")
    else:
        st.warning("No pre-trained model found. Training new model...")
        preprocessor, engineer, featured_data = load_and_prepare_data()
        X_train, y_train, X_test, y_test = engineer.prepare_ml_data(featured_data)

        predictor = BinFillPredictor(n_estimators=100, max_depth=20)
        predictor.train(X_train, y_train)
        predictor.evaluate(X_test, y_test)

        os.makedirs('models', exist_ok=True)
        predictor.save_model(model_path)
        st.success("✓ Model trained and saved")

    return predictor


def main():
    """Main dashboard application"""

    # Header
    st.markdown('<p class="main-header">🗑️ Dynamic Waste Collection Route Optimization</p>',
                unsafe_allow_html=True)
    st.markdown("### Using Predictive Analytics & Machine Learning")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Data source
        st.subheader("Data Source")
        use_sample_data = st.checkbox("Use sample data", value=True)

        # Prediction parameters
        st.subheader("Prediction Parameters")
        hours_ahead = st.slider("Predict hours ahead", 1, 48, 24)
        collection_threshold = st.slider("Collection threshold (%)", 50, 95, 80)

        # Route optimization parameters
        st.subheader("Route Optimization")
        num_vehicles = st.slider("Number of vehicles", 1, 5, 3)
        vehicle_capacity = st.slider("Vehicle capacity (bins)", 5, 20, 10)

        # Depot location
        st.subheader("Depot Location")
        depot_lat = st.number_input("Latitude", value=51.5294, format="%.4f")
        depot_lon = st.number_input("Longitude", value=-0.1194, format="%.4f")

        # Run optimization button
        run_optimization = st.button("🚀 Run Optimization", type="primary")

    # Main content area
    tabs = st.tabs(["📊 Dashboard", "🗺️ Map View", "📈 Analytics", "⚙️ Model Info"])

    # Load data
    preprocessor, engineer, featured_data = load_and_prepare_data()
    latest_status = preprocessor.get_latest_status()

    with tabs[0]:  # Dashboard
        st.header("Current System Status")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Bins", len(latest_status))

        with col2:
            avg_fill = latest_status['fill_percentage'].mean()
            st.metric("Average Fill Level", f"{avg_fill:.1f}%")

        with col3:
            bins_over_80 = len(latest_status[latest_status['fill_percentage'] >= 80])
            st.metric("Bins ≥80% Full", bins_over_80)

        with col4:
            bins_critical = len(latest_status[latest_status['fill_percentage'] >= 90])
            st.metric("Critical Bins (≥90%)", bins_critical)

        st.divider()

        # Fill level distribution
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Fill Level Distribution")
            fig = px.histogram(
                latest_status,
                x='fill_percentage',
                nbins=20,
                title="Current Fill Levels",
                labels={'fill_percentage': 'Fill Percentage (%)', 'count': 'Number of Bins'}
            )
            fig.update_traces(marker_color='#1f77b4')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Bins by Type")
            if 'bin_type' in latest_status.columns:
                type_counts = latest_status['bin_type'].value_counts()
                fig = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title="Bin Type Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Bin type information not available")

        # Recent trends
        st.subheader("Fill Level Trends")
        trend_data = featured_data.groupby('timestamp')['fill_percentage'].mean().reset_index()
        fig = px.line(
            trend_data,
            x='timestamp',
            y='fill_percentage',
            title="Average Fill Level Over Time"
        )
        fig.update_layout(yaxis_range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:  # Map View
        st.header("Geographical View")

        if run_optimization:
            with st.spinner("Running predictions and route optimization..."):
                try:
                    # Load model
                    predictor = load_model()

                    # Make predictions
                    # Prepare features for latest status
                    latest_featured = engineer.create_all_features(
                        preprocessor.data[preprocessor.data['bin_id'].isin(latest_status['bin_id'])]
                    )
                    latest_featured = latest_featured.groupby('bin_id').tail(1)

                    # Get feature columns
                    exclude_cols = ['bin_id', 'timestamp', 'fill_percentage', 'bin_type',
                                  'latitude', 'longitude']
                    feature_cols = [col for col in latest_featured.columns if col not in exclude_cols]

                    if len(feature_cols) > 0:
                        X_predict = latest_featured[feature_cols]
                        predictions = predictor.predict(X_predict)

                        # Add predictions to latest status
                        latest_status['predicted_fill'] = predictions

                        # Route optimization
                        router = WasteCollectionRouter(
                            depot_location=(depot_lat, depot_lon),
                            vehicle_capacity=vehicle_capacity,
                            num_vehicles=num_vehicles
                        )

                        bins_to_collect = router.get_bins_needing_collection(
                            latest_status,
                            threshold=collection_threshold
                        )

                        if len(bins_to_collect) > 0:
                            result = router.optimize_routes(bins_to_collect, time_limit_seconds=30)

                            # Display results
                            st.success(f"✓ Optimization complete!")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Vehicles Used", result['num_vehicles_used'])
                            with col2:
                                st.metric("Bins to Collect", result['total_bins_collected'])
                            with col3:
                                st.metric("Total Distance", f"{result['total_distance_km']} km")

                            # Route details
                            st.subheader("Route Details")
                            for route in result['routes']:
                                with st.expander(f"Vehicle {route['vehicle_id']} - {route['num_bins']} bins, {route['distance_km']} km"):
                                    stops_df = pd.DataFrame(route['stops'])
                                    st.dataframe(stops_df)

                            # Create map
                            visualizer = RouteMapVisualizer(center_location=(depot_lat, depot_lon))
                            map_file = 'optimized_routes.html'
                            visualizer.visualize_routes(result, latest_status, (depot_lat, depot_lon), map_file)

                            # Display map
                            with open(map_file, 'r') as f:
                                map_html = f.read()
                            st.components.v1.html(map_html, height=600, scrolling=True)

                        else:
                            st.info("No bins need collection at the moment.")
                    else:
                        st.error("Could not extract features for prediction")

                except Exception as e:
                    st.error(f"Error during optimization: {str(e)}")
        else:
            # Show current bin status map
            visualizer = RouteMapVisualizer(center_location=(depot_lat, depot_lon))
            map_file = 'bin_status.html'
            visualizer.visualize_bin_status(latest_status, map_file)

            with open(map_file, 'r') as f:
                map_html = f.read()
            st.components.v1.html(map_html, height=600, scrolling=True)

            st.info("Click 'Run Optimization' in the sidebar to see optimized routes")

    with tabs[2]:  # Analytics
        st.header("Analytics & Insights")

        # Bin performance
        st.subheader("Bin Fill Rate Analysis")

        bin_stats = featured_data.groupby('bin_id').agg({
            'fill_percentage': ['mean', 'max', 'std'],
            'fill_rate': 'mean'
        }).reset_index()
        bin_stats.columns = ['bin_id', 'avg_fill', 'max_fill', 'std_fill', 'avg_rate']

        # Top bins by fill rate
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top 10 Fastest Filling Bins")
            if 'fill_rate' in bin_stats.columns:
                top_bins = bin_stats.nlargest(10, 'avg_rate')
                fig = px.bar(
                    top_bins,
                    x='bin_id',
                    y='avg_rate',
                    title="Average Fill Rate (% per hour)"
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Most Variable Bins")
            top_variable = bin_stats.nlargest(10, 'std_fill')
            fig = px.bar(
                top_variable,
                x='bin_id',
                y='std_fill',
                title="Fill Level Standard Deviation"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Time patterns
        st.subheader("Time-based Patterns")
        hourly_pattern = featured_data.groupby('hour')['fill_percentage'].mean().reset_index()
        fig = px.line(
            hourly_pattern,
            x='hour',
            y='fill_percentage',
            title="Average Fill Level by Hour of Day"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Weekly pattern
        weekly_pattern = featured_data.groupby('day_of_week')['fill_percentage'].mean().reset_index()
        weekly_pattern['day_name'] = weekly_pattern['day_of_week'].map({
            0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
            4: 'Friday', 5: 'Saturday', 6: 'Sunday'
        })
        fig = px.bar(
            weekly_pattern,
            x='day_name',
            y='fill_percentage',
            title="Average Fill Level by Day of Week"
        )
        st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:  # Model Info
        st.header("Model Information")

        # Load model
        predictor = load_model()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Model Parameters")
            st.write(f"**Model Type:** Random Forest Regressor")
            st.write(f"**Number of Trees:** {predictor.model.n_estimators}")
            st.write(f"**Max Depth:** {predictor.model.max_depth}")

            if predictor.metrics:
                st.subheader("Performance Metrics")
                st.metric("RMSE", f"{predictor.metrics.get('rmse', 0):.2f}%")
                st.metric("MAE", f"{predictor.metrics.get('mae', 0):.2f}%")
                st.metric("R² Score", f"{predictor.metrics.get('r2', 0):.4f}")

        with col2:
            st.subheader("Feature Importance")
            if predictor.feature_importance is not None:
                top_features = predictor.feature_importance.head(10)
                fig = px.bar(
                    top_features,
                    x='importance',
                    y='feature',
                    orientation='h',
                    title="Top 10 Most Important Features"
                )
                st.plotly_chart(fig, use_container_width=True)

        # Data info
        st.subheader("Dataset Information")
        st.write(f"**Total Records:** {len(featured_data):,}")
        st.write(f"**Number of Bins:** {featured_data['bin_id'].nunique()}")
        st.write(f"**Date Range:** {featured_data['timestamp'].min()} to {featured_data['timestamp'].max()}")
        st.write(f"**Features:** {len([col for col in featured_data.columns if col not in ['bin_id', 'timestamp', 'fill_percentage', 'latitude', 'longitude', 'bin_type']])}")


if __name__ == "__main__":
    main()
