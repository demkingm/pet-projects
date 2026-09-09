"""
Модуль маршрутизации для распределения точек по менеджерам и дням.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict


def assign_managers_by_clusters(
    df: pd.DataFrame,
    n_managers: int = 3,
    cluster_col: str = 'cluster_id',
    manager_col: str = 'manager'
) -> pd.DataFrame:
    """Распределяет кластеры между менеджерами."""
    if cluster_col not in df.columns:
        raise ValueError(f"Колонка '{cluster_col}' не найдена")
    
    result_df = df.copy()
    result_df[manager_col] = -1
    
    clusters = result_df[cluster_col].unique()
    cluster_sizes = result_df.groupby(cluster_col).size().to_dict()
    clusters_sorted = sorted(clusters, key=lambda x: cluster_sizes.get(x, 0), reverse=True)
    
    manager_idx = 0
    for cluster in clusters_sorted:
        mask = result_df[cluster_col] == cluster
        result_df.loc[mask, manager_col] = manager_idx % n_managers
        manager_idx += 1
    
    return result_df


def create_daily_schedule(
    df: pd.DataFrame,
    max_points_per_day: int = 10,
    n_managers: int = 3,
    day_col: str = 'visit_day',
    sort_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Создает расписание по дням для каждого менеджера.
    
    Исправленная версия: учитывает общий лимит в день (n_managers * max_points_per_day)
    """
    result_df = df.copy()
    
    if 'manager' not in result_df.columns:
        raise ValueError("Колонка 'manager' не найдена")
    
    if sort_cols is None:
        sort_cols = ['manager', 'cluster_id' if 'cluster_id' in result_df.columns else 'lat']
    
    result_df = result_df.sort_values(sort_cols).reset_index(drop=True)
    result_df[day_col] = -1
    
    # Словарь для отслеживания занятости дней
    # Ключ: (manager, day), Значение: количество точек
    day_load = {}
    
    for manager in result_df['manager'].unique():
        mask = result_df['manager'] == manager
        manager_indices = result_df[mask].index
        
        for idx in manager_indices:
            # Ищем первый свободный день для этого менеджера
            day = 1
            while True:
                # Проверяем, не превышен ли лимит для этого менеджера в этот день
                current_load = day_load.get((manager, day), 0)
                
                if current_load < max_points_per_day:
                    # Проверяем общий лимит в день (все менеджеры)
                    total_day_load = sum(
                        day_load.get((m, day), 0) 
                        for m in range(int(result_df['manager'].max()) + 1)
                    )
                    
                    if total_day_load < max_points_per_day * n_managers:
                        # Назначаем день
                        result_df.loc[idx, day_col] = day
                        day_load[(manager, day)] = current_load + 1
                        break
                    else:
                        # День переполнен, пробуем следующий
                        day += 1
                else:
                    # У этого менеджера уже 10 точек в этот день
                    day += 1
    
    return result_df


def calculate_route_order(
    df: pd.DataFrame,
    lat_col: str = 'lat',
    lon_col: str = 'lon',
    order_col: str = 'order_in_route'
) -> pd.DataFrame:
    """Рассчитывает порядок точек в маршруте."""
    required_cols = ['manager', 'visit_day', lat_col, lon_col]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Колонка '{col}' не найдена")
    
    from haversine import haversine, Unit
    
    result_df = df.copy()
    result_df[order_col] = -1
    
    groups = result_df.groupby(['manager', 'visit_day'])
    
    for (manager, day), group in groups:
        indices = group.index
        
        if len(indices) <= 1:
            result_df.loc[indices, order_col] = 0
            continue
        
        coords = group[[lat_col, lon_col]].values
        ordered_indices = []
        remaining = list(range(len(indices)))
        
        current = 0
        ordered_indices.append(remaining.pop(current))
        
        while remaining:
            current_coord = coords[ordered_indices[-1]]
            distances = []
            
            for i in remaining:
                dist = haversine(
                    (current_coord[0], current_coord[1]),
                    (coords[i][0], coords[i][1]),
                    unit=Unit.KILOMETERS
                )
                distances.append((i, dist))
            
            nearest = min(distances, key=lambda x: x[1])[0]
            ordered_indices.append(remaining.pop(remaining.index(nearest)))
        
        for order, idx in enumerate(ordered_indices):
            result_df.loc[indices[idx], order_col] = order
    
    return result_df


def create_route(
    df: pd.DataFrame,
    max_points_per_day: int = 10,
    n_managers: int = 3
) -> pd.DataFrame:
    """
    Создает полный маршрут для всех менеджеров.
    Исправленная версия с правильным распределением по дням.
    """
    from .clustering import cluster_points
    
    if 'point_id' not in df.columns:
        raise ValueError("Колонка 'point_id' не найдена")
    if 'lat' not in df.columns or 'lon' not in df.columns:
        raise ValueError("Требуются колонки 'lat' и 'lon'")
    
    # 1. Кластеризация
    clustered = cluster_points(df, max_points_per_cluster=max_points_per_day)
    
    # 2. Распределение по менеджерам
    with_managers = assign_managers_by_clusters(clustered, n_managers=n_managers)
    
    # 3. Создание расписания по дням (исправленная версия)
    with_days = create_daily_schedule(
        with_managers,
        max_points_per_day=max_points_per_day,
        n_managers=n_managers
    )
    
    # 4. Расчет порядка в маршруте
    final_route = calculate_route_order(with_days)
    
    result_cols = ['point_id', 'visit_day', 'cluster_id', 'order_in_route']
    result = final_route[result_cols].copy()
    
    # Добавляем manager для удобства
    result['manager'] = final_route['manager']
    
    return result


def validate_route(route: pd.DataFrame) -> dict:
    """Проверяет корректность маршрута."""
    results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'max_points_per_day': 0,
        'days_with_exceed': []
    }
    
    required_cols = ['point_id', 'visit_day', 'cluster_id', 'order_in_route', 'manager']
    for col in required_cols:
        if col not in route.columns:
            results['is_valid'] = False
            results['errors'].append(f"Отсутствует колонка '{col}'")
    
    if len(route['point_id'].unique()) != len(route):
        results['is_valid'] = False
        results['errors'].append("Есть дублирующиеся point_id")
    
    # Проверка лимита по дням
    day_stats = route.groupby(['manager', 'visit_day']).size().unstack(fill_value=0)
    max_per_day = day_stats.max().max()
    results['max_points_per_day'] = max_per_day
    
    if max_per_day > 10:
        results['is_valid'] = False
        results['errors'].append(f"Превышение лимита: максимум {max_per_day} точек в день")
        
        # Находим проблемные дни
        for manager in day_stats.index:
            for day in day_stats.columns:
                if day_stats.loc[manager, day] > 10:
                    results['days_with_exceed'].append({
                        'manager': manager,
                        'day': day,
                        'points': day_stats.loc[manager, day]
                    })
    
    return results