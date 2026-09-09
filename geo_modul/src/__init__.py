"""
Geo Project - модули для кластеризации и маршрутизации.
"""

from .clustering import cluster_points, get_cluster_statistics
from .routing import create_route, assign_managers_by_clusters, create_daily_schedule, calculate_route_order
from .visualize import create_map, plot_cluster_statistics, create_route_animation, create_simple_scatter

__version__ = '1.0.0'
__all__ = [
    'cluster_points',
    'get_cluster_statistics',
    'create_route',
    'assign_managers_by_clusters',
    'create_daily_schedule',
    'calculate_route_order',
    'create_map',
    'plot_cluster_statistics',
    'create_route_animation',
    'create_simple_scatter'
]