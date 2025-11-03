"""
Route optimization using Google OR-Tools for waste collection
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from geopy.distance import geodesic

try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    print("Warning: OR-Tools not available. Route optimization will not work.")


class WasteCollectionRouter:
    """Route optimizer for waste collection using Vehicle Routing Problem (VRP)"""

    def __init__(self, depot_location: Tuple[float, float] = (51.5294, -0.1194),
                 vehicle_capacity: int = 10, num_vehicles: int = 3):
        """
        Initialize route optimizer

        Args:
            depot_location: (latitude, longitude) of depot/starting point
            vehicle_capacity: Maximum number of bins a vehicle can collect
            num_vehicles: Number of vehicles available
        """
        if not ORTOOLS_AVAILABLE:
            raise ImportError("OR-Tools is required for route optimization")

        self.depot_location = depot_location
        self.vehicle_capacity = vehicle_capacity
        self.num_vehicles = num_vehicles
        self.distance_matrix = None
        self.locations = []
        self.bin_ids = []

    def calculate_distance_matrix(self, bins_df: pd.DataFrame) -> np.ndarray:
        """
        Calculate distance matrix between all locations

        Args:
            bins_df: DataFrame with bin locations (latitude, longitude)

        Returns:
            Distance matrix in kilometers
        """
        # Include depot as first location
        locations = [(self.depot_location[0], self.depot_location[1])]
        bin_ids = ['DEPOT']

        # Add bin locations
        for _, row in bins_df.iterrows():
            locations.append((row['latitude'], row['longitude']))
            bin_ids.append(row['bin_id'])

        self.locations = locations
        self.bin_ids = bin_ids

        n = len(locations)
        distance_matrix = np.zeros((n, n))

        # Calculate distances
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist = geodesic(locations[i], locations[j]).kilometers
                    distance_matrix[i][j] = dist

        # Convert to integer (meters) for OR-Tools
        self.distance_matrix = (distance_matrix * 1000).astype(int)

        print(f"✓ Distance matrix calculated for {n} locations (including depot)")
        return self.distance_matrix

    def create_data_model(self, bins_df: pd.DataFrame) -> Dict:
        """
        Create data model for OR-Tools

        Args:
            bins_df: DataFrame with bins that need collection

        Returns:
            Data model dictionary
        """
        if self.distance_matrix is None:
            self.calculate_distance_matrix(bins_df)

        data = {
            'distance_matrix': self.distance_matrix.tolist(),
            'num_vehicles': self.num_vehicles,
            'depot': 0,  # Depot is the first location (index 0)
            'demands': [0] + [1] * (len(self.locations) - 1),  # Each bin = 1 unit
            'vehicle_capacities': [self.vehicle_capacity] * self.num_vehicles
        }

        return data

    def optimize_routes(self, bins_df: pd.DataFrame, time_limit_seconds: int = 30) -> Dict:
        """
        Optimize collection routes for bins

        Args:
            bins_df: DataFrame with bins that need collection (predicted >= 80% full)
            time_limit_seconds: Maximum time for optimization

        Returns:
            Dictionary with optimized routes
        """
        if len(bins_df) == 0:
            print("No bins need collection")
            return {'routes': [], 'total_distance': 0}

        print(f"\nOptimizing routes for {len(bins_df)} bins...")

        # Create data model
        data = self.create_data_model(bins_df)

        # Create routing index manager
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['depot']
        )

        # Create routing model
        routing = pywrapcp.RoutingModel(manager)

        # Create distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)

        # Define cost of each arc
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add capacity constraint
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],
            True,  # start cumul to zero
            'Capacity'
        )

        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = time_limit_seconds

        # Solve the problem
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            return self._extract_solution(manager, routing, solution, bins_df)
        else:
            print("No solution found!")
            return {'routes': [], 'total_distance': 0}

    def _extract_solution(self, manager, routing, solution, bins_df: pd.DataFrame) -> Dict:
        """
        Extract solution from OR-Tools solver

        Args:
            manager: Routing index manager
            routing: Routing model
            solution: Solution object
            bins_df: Original bins DataFrame

        Returns:
            Dictionary with routes information
        """
        routes = []
        total_distance = 0

        for vehicle_id in range(self.num_vehicles):
            index = routing.Start(vehicle_id)
            route = {
                'vehicle_id': vehicle_id + 1,
                'stops': [],
                'distance_km': 0,
                'num_bins': 0
            }

            route_distance = 0

            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)

                if node_index > 0:  # Skip depot
                    bin_id = self.bin_ids[node_index]
                    bin_info = bins_df[bins_df['bin_id'] == bin_id].iloc[0]

                    route['stops'].append({
                        'bin_id': bin_id,
                        'location': (bin_info['latitude'], bin_info['longitude']),
                        'predicted_fill': bin_info.get('predicted_fill', bin_info.get('fill_percentage', 0))
                    })

                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)

            route['distance_km'] = round(route_distance / 1000, 2)
            route['num_bins'] = len(route['stops'])

            if route['num_bins'] > 0:
                routes.append(route)
                total_distance += route['distance_km']

        result = {
            'routes': routes,
            'total_distance_km': round(total_distance, 2),
            'num_vehicles_used': len([r for r in routes if r['num_bins'] > 0]),
            'total_bins_collected': sum(r['num_bins'] for r in routes)
        }

        print(f"\n✓ Route optimization complete!")
        print(f"  Vehicles used: {result['num_vehicles_used']}/{self.num_vehicles}")
        print(f"  Total bins: {result['total_bins_collected']}")
        print(f"  Total distance: {result['total_distance_km']} km")

        for i, route in enumerate(routes):
            print(f"  Vehicle {route['vehicle_id']}: {route['num_bins']} bins, {route['distance_km']} km")

        return result

    def get_bins_needing_collection(self, predictions_df: pd.DataFrame,
                                   threshold: float = 80.0) -> pd.DataFrame:
        """
        Filter bins that need collection based on prediction

        Args:
            predictions_df: DataFrame with predicted fill levels
            threshold: Fill percentage threshold for collection

        Returns:
            DataFrame with bins needing collection
        """
        needs_collection = predictions_df[
            predictions_df['predicted_fill'] >= threshold
        ].copy()

        print(f"✓ {len(needs_collection)} bins need collection (>= {threshold}% full)")

        return needs_collection


class RouteAnalyzer:
    """Analyze and compare different routing strategies"""

    @staticmethod
    def calculate_route_metrics(route: Dict) -> Dict[str, float]:
        """Calculate metrics for a route"""
        if len(route['stops']) == 0:
            return {
                'avg_distance_per_stop': 0,
                'efficiency_score': 0
            }

        avg_distance = route['distance_km'] / route['num_bins'] if route['num_bins'] > 0 else 0

        # Efficiency score: bins collected per km
        efficiency = route['num_bins'] / route['distance_km'] if route['distance_km'] > 0 else 0

        return {
            'avg_distance_per_stop': round(avg_distance, 2),
            'efficiency_score': round(efficiency, 2)
        }

    @staticmethod
    def compare_strategies(optimized_result: Dict, random_result: Dict = None) -> pd.DataFrame:
        """
        Compare optimized routes with baseline

        Args:
            optimized_result: Result from optimized routing
            random_result: Result from random/baseline routing

        Returns:
            Comparison DataFrame
        """
        comparison = []

        # Optimized
        comparison.append({
            'strategy': 'Optimized (OR-Tools)',
            'total_distance_km': optimized_result['total_distance_km'],
            'vehicles_used': optimized_result['num_vehicles_used'],
            'bins_collected': optimized_result['total_bins_collected'],
            'avg_distance_per_bin': round(
                optimized_result['total_distance_km'] / optimized_result['total_bins_collected']
                if optimized_result['total_bins_collected'] > 0 else 0, 2
            )
        })

        if random_result:
            comparison.append({
                'strategy': 'Baseline',
                'total_distance_km': random_result['total_distance_km'],
                'vehicles_used': random_result['num_vehicles_used'],
                'bins_collected': random_result['total_bins_collected'],
                'avg_distance_per_bin': round(
                    random_result['total_distance_km'] / random_result['total_bins_collected']
                    if random_result['total_bins_collected'] > 0 else 0, 2
                )
            })

            # Calculate improvement
            if comparison[1]['total_distance_km'] > 0:
                improvement = (1 - comparison[0]['total_distance_km'] / comparison[1]['total_distance_km']) * 100
                print(f"\n✓ Distance reduction: {improvement:.1f}%")

        return pd.DataFrame(comparison)


if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.append('..')

    from src.data.preprocessing import BinDataPreprocessor
    from src.models.random_forest_model import BinFillPredictor

    # Load data
    preprocessor = BinDataPreprocessor()
    data = preprocessor.load_data('data/raw/smart-bins-argyle-square.csv')

    # Get latest status
    latest_status = preprocessor.get_latest_status()

    # Simulate predictions (in real scenario, use trained model)
    latest_status['predicted_fill'] = latest_status['fill_percentage'] + np.random.uniform(5, 15, len(latest_status))

    # Initialize router
    router = WasteCollectionRouter(
        depot_location=(51.5294, -0.1194),
        vehicle_capacity=10,
        num_vehicles=3
    )

    # Get bins needing collection
    bins_to_collect = router.get_bins_needing_collection(latest_status, threshold=80)

    # Optimize routes
    if len(bins_to_collect) > 0:
        result = router.optimize_routes(bins_to_collect, time_limit_seconds=30)
        print("\nOptimized routes:", result)
