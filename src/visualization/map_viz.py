"""
Map visualization using Folium for waste collection routes
"""

import folium
from folium import plugins
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import os


class RouteMapVisualizer:
    """Visualize waste collection routes on interactive maps"""

    def __init__(self, center_location: Tuple[float, float] = (51.5294, -0.1194)):
        """
        Initialize map visualizer

        Args:
            center_location: (latitude, longitude) for map center
        """
        self.center_location = center_location
        self.color_palette = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A',
            '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2'
        ]

    def create_base_map(self, zoom_start: int = 14) -> folium.Map:
        """
        Create base map

        Args:
            zoom_start: Initial zoom level

        Returns:
            Folium map object
        """
        m = folium.Map(
            location=self.center_location,
            zoom_start=zoom_start,
            tiles='OpenStreetMap'
        )
        return m

    def add_depot_marker(self, m: folium.Map, depot_location: Tuple[float, float]):
        """
        Add depot marker to map

        Args:
            m: Folium map object
            depot_location: (latitude, longitude) of depot
        """
        folium.Marker(
            location=depot_location,
            popup='<b>Depot</b><br>Collection Center',
            tooltip='Depot',
            icon=folium.Icon(color='red', icon='home', prefix='fa')
        ).add_to(m)

    def get_fill_color(self, fill_percentage: float) -> str:
        """
        Get color based on fill percentage

        Args:
            fill_percentage: Fill percentage (0-100)

        Returns:
            Color string
        """
        if fill_percentage < 50:
            return 'green'
        elif fill_percentage < 70:
            return 'orange'
        elif fill_percentage < 90:
            return 'red'
        else:
            return 'darkred'

    def add_bin_markers(self, m: folium.Map, bins_df: pd.DataFrame,
                       show_predictions: bool = True):
        """
        Add bin markers to map

        Args:
            m: Folium map object
            bins_df: DataFrame with bin information
            show_predictions: Whether to show prediction info
        """
        for _, bin_row in bins_df.iterrows():
            fill_col = 'predicted_fill' if 'predicted_fill' in bin_row and show_predictions else 'fill_percentage'
            fill_level = bin_row.get(fill_col, 0)

            # Create popup text
            popup_text = f"""
            <div style="width: 200px">
                <b>{bin_row['bin_id']}</b><br>
                {'Predicted' if show_predictions and 'predicted_fill' in bin_row else 'Current'} Fill: {fill_level:.1f}%<br>
            """

            if 'current_fill' in bin_row and show_predictions:
                popup_text += f"Current Fill: {bin_row['current_fill']:.1f}%<br>"

            if 'bin_type' in bin_row:
                popup_text += f"Type: {bin_row['bin_type']}<br>"

            if 'capacity_liters' in bin_row:
                popup_text += f"Capacity: {bin_row['capacity_liters']}L<br>"

            popup_text += "</div>"

            # Get color based on fill level
            color = self.get_fill_color(fill_level)

            # Create marker
            folium.CircleMarker(
                location=(bin_row['latitude'], bin_row['longitude']),
                radius=8,
                popup=folium.Popup(popup_text, max_width=250),
                tooltip=f"{bin_row['bin_id']}: {fill_level:.1f}%",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)

    def add_route(self, m: folium.Map, route: Dict, depot_location: Tuple[float, float],
                  vehicle_id: int):
        """
        Add a single route to map

        Args:
            m: Folium map object
            route: Route dictionary with stops
            depot_location: (latitude, longitude) of depot
            vehicle_id: Vehicle ID for color selection
        """
        if len(route['stops']) == 0:
            return

        # Get color for this vehicle
        color = self.color_palette[vehicle_id % len(self.color_palette)]

        # Create route path
        route_coords = [depot_location]
        for stop in route['stops']:
            route_coords.append(stop['location'])
        route_coords.append(depot_location)  # Return to depot

        # Draw route line
        folium.PolyLine(
            locations=route_coords,
            color=color,
            weight=3,
            opacity=0.8,
            tooltip=f"Vehicle {vehicle_id + 1}: {route['distance_km']} km"
        ).add_to(m)

        # Add numbered markers for stops
        for idx, stop in enumerate(route['stops'], 1):
            folium.Marker(
                location=stop['location'],
                icon=folium.DivIcon(html=f"""
                    <div style="
                        background-color: {color};
                        color: white;
                        border-radius: 50%;
                        width: 25px;
                        height: 25px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        border: 2px solid white;
                        box-shadow: 0 0 4px rgba(0,0,0,0.5);
                    ">{idx}</div>
                """),
                popup=f"""
                <b>Stop {idx}</b><br>
                Bin: {stop['bin_id']}<br>
                Fill: {stop['predicted_fill']:.1f}%
                """
            ).add_to(m)

    def visualize_routes(self, routes_result: Dict, bins_df: pd.DataFrame,
                        depot_location: Tuple[float, float],
                        save_path: str = 'routes_map.html') -> folium.Map:
        """
        Visualize all optimized routes

        Args:
            routes_result: Result from route optimizer
            bins_df: DataFrame with all bins
            depot_location: (latitude, longitude) of depot
            save_path: Path to save HTML map

        Returns:
            Folium map object
        """
        # Create base map
        m = self.create_base_map()

        # Add depot
        self.add_depot_marker(m, depot_location)

        # Add all bin markers
        self.add_bin_markers(m, bins_df, show_predictions=True)

        # Add routes
        for i, route in enumerate(routes_result['routes']):
            self.add_route(m, route, depot_location, i)

        # Add legend
        legend_html = f"""
        <div style="position: fixed;
                    bottom: 50px; right: 50px; width: 200px; height: auto;
                    background-color: white; border:2px solid grey; z-index:9999;
                    padding: 10px; font-size: 14px; border-radius: 5px;">
            <h4 style="margin-top:0">Route Summary</h4>
            <p><b>Total Distance:</b> {routes_result['total_distance_km']} km</p>
            <p><b>Vehicles Used:</b> {routes_result['num_vehicles_used']}</p>
            <p><b>Bins Collected:</b> {routes_result['total_bins_collected']}</p>
            <hr>
            <p style="font-size: 12px;">
                <span style="color: green;">●</span> &lt; 50% Full<br>
                <span style="color: orange;">●</span> 50-70% Full<br>
                <span style="color: red;">●</span> 70-90% Full<br>
                <span style="color: darkred;">●</span> &gt; 90% Full
            </p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        # Add fullscreen option
        plugins.Fullscreen().add_to(m)

        # Save map
        m.save(save_path)
        print(f"✓ Route map saved to {save_path}")

        return m

    def visualize_bin_status(self, bins_df: pd.DataFrame,
                            save_path: str = 'bin_status_map.html') -> folium.Map:
        """
        Visualize current/predicted bin status

        Args:
            bins_df: DataFrame with bin information
            save_path: Path to save HTML map

        Returns:
            Folium map object
        """
        # Create base map centered on bins
        if len(bins_df) > 0:
            center_lat = bins_df['latitude'].mean()
            center_lon = bins_df['longitude'].mean()
            m = folium.Map(location=(center_lat, center_lon), zoom_start=14)
        else:
            m = self.create_base_map()

        # Add bin markers
        self.add_bin_markers(m, bins_df, show_predictions='predicted_fill' in bins_df.columns)

        # Add marker cluster for better performance with many bins
        if len(bins_df) > 50:
            marker_cluster = plugins.MarkerCluster().add_to(m)
            for _, bin_row in bins_df.iterrows():
                fill_col = 'predicted_fill' if 'predicted_fill' in bin_row else 'fill_percentage'
                fill_level = bin_row.get(fill_col, 0)
                color = self.get_fill_color(fill_level)

                folium.Marker(
                    location=(bin_row['latitude'], bin_row['longitude']),
                    popup=f"{bin_row['bin_id']}: {fill_level:.1f}%",
                    icon=folium.Icon(color=color)
                ).add_to(marker_cluster)

        # Add heatmap for fill levels
        if len(bins_df) > 0:
            fill_col = 'predicted_fill' if 'predicted_fill' in bins_df.columns else 'fill_percentage'
            heat_data = [[row['latitude'], row['longitude'], row[fill_col]/100]
                        for _, row in bins_df.iterrows()]

            plugins.HeatMap(heat_data, radius=15, blur=20, max_zoom=13).add_to(m)

        # Add fullscreen option
        plugins.Fullscreen().add_to(m)

        # Save map
        m.save(save_path)
        print(f"✓ Bin status map saved to {save_path}")

        return m

    def create_comparison_map(self, before_df: pd.DataFrame, after_df: pd.DataFrame,
                             save_path: str = 'comparison_map.html') -> folium.Map:
        """
        Create side-by-side comparison map

        Args:
            before_df: Bin status before collection
            after_df: Bin status after collection
            save_path: Path to save HTML map

        Returns:
            Folium map object
        """
        # Calculate center
        all_lats = list(before_df['latitude']) + list(after_df['latitude'])
        all_lons = list(before_df['longitude']) + list(after_df['longitude'])
        center_lat = np.mean(all_lats)
        center_lon = np.mean(all_lons)

        # Create map
        m = folium.Map(location=(center_lat, center_lon), zoom_start=13)

        # Add before markers
        for _, bin_row in before_df.iterrows():
            fill_level = bin_row.get('predicted_fill', bin_row.get('fill_percentage', 0))
            folium.CircleMarker(
                location=(bin_row['latitude'], bin_row['longitude']),
                radius=6,
                popup=f"Before: {bin_row['bin_id']} - {fill_level:.1f}%",
                color='red',
                fill=True,
                fillOpacity=0.4
            ).add_to(m)

        # Add after markers
        for _, bin_row in after_df.iterrows():
            fill_level = bin_row.get('fill_percentage', 0)
            folium.CircleMarker(
                location=(bin_row['latitude'], bin_row['longitude']),
                radius=6,
                popup=f"After: {bin_row['bin_id']} - {fill_level:.1f}%",
                color='green',
                fill=True,
                fillOpacity=0.6
            ).add_to(m)

        m.save(save_path)
        print(f"✓ Comparison map saved to {save_path}")

        return m


if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.append('..')

    from src.data.preprocessing import BinDataPreprocessor

    # Load sample data
    preprocessor = BinDataPreprocessor()
    data = preprocessor.load_data('data/raw/smart-bins-argyle-square.csv')
    latest_status = preprocessor.get_latest_status()

    # Add predictions (simulated)
    latest_status['predicted_fill'] = latest_status['fill_percentage'] + np.random.uniform(5, 15, len(latest_status))

    # Create visualizations
    visualizer = RouteMapVisualizer(center_location=(51.5294, -0.1194))

    # Visualize bin status
    visualizer.visualize_bin_status(latest_status, save_path='bin_status_map.html')

    print("Maps created successfully!")
