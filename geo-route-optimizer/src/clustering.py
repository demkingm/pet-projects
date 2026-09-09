"""
Модуль кластеризации для группировки географических точек.

Содержит функции для кластеризации точек по географическим координатам
с использованием алгоритма KMeans.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from typing import Optional, Tuple


def cluster_points(
    df: pd.DataFrame,
    lat_col: str = 'lat',
    lon_col: str = 'lon',
    max_points_per_cluster: int = 10,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Кластеризует точки по географическим координатам.
    
    Количество кластеров определяется автоматически на основе общего числа точек
    и максимального размера кластера.
    
    Parameters
    ----------
    df : pd.DataFrame
        Датафрейм с координатами точек
    lat_col : str, default='lat'
        Название колонки с широтой
    lon_col : str, default='lon'
        Название колонки с долготой
    max_points_per_cluster : int, default=10
        Максимальное количество точек в одном кластере
    random_state : int, default=42
        Seed для воспроизводимости результатов
    
    Returns
    -------
    pd.DataFrame
        Исходный датафрейм с добавленной колонкой 'cluster_id'
    
    Examples
    --------
    >>> df = pd.DataFrame({
    ...     'lat': [55.37, 55.35, 55.37],
    ...     'lon': [43.84, 43.84, 43.83]
    ... })
    >>> result = cluster_points(df, max_points_per_cluster=2)
    >>> result['cluster_id'].unique()
    array([0, 1])
    """
    # Проверка входных данных
    if len(df) == 0:
        df = df.copy()
        df['cluster_id'] = np.nan
        return df
    
    # Проверка наличия колонок
    if lat_col not in df.columns:
        raise ValueError(f"Колонка '{lat_col}' не найдена в данных")
    if lon_col not in df.columns:
        raise ValueError(f"Колонка '{lon_col}' не найдена в данных")
    
    # Извлечение координат
    coords = df[[lat_col, lon_col]].values
    n_points = len(df)
    
    # Расчет количества кластеров
    n_clusters = max(1, int(np.ceil(n_points / max_points_per_cluster)))
    
    # Кластеризация
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=10
    )
    labels = kmeans.fit_predict(coords)
    
    # Добавление результатов
    result_df = df.copy()
    result_df['cluster_id'] = labels
    
    return result_df


def get_cluster_statistics(df: pd.DataFrame, cluster_col: str = 'cluster_id') -> pd.DataFrame:
    """
    Получает статистику по кластерам.
    
    Parameters
    ----------
    df : pd.DataFrame
        Датафрейм с колонкой кластеров
    cluster_col : str, default='cluster_id'
        Название колонки с идентификаторами кластеров
    
    Returns
    -------
    pd.DataFrame
        Статистика по кластерам (размер, центр, разброс)
    
    Examples
    --------
    >>> df = pd.DataFrame({
    ...     'lat': [55.37, 55.35, 55.37],
    ...     'lon': [43.84, 43.84, 43.83],
    ...     'cluster_id': [0, 0, 1]
    ... })
    >>> stats = get_cluster_statistics(df)
    >>> stats.columns.tolist()
    ['cluster_id', 'size', 'center_lat', 'center_lon', 'radius_km']
    """
    if cluster_col not in df.columns:
        raise ValueError(f"Колонка '{cluster_col}' не найдена в данных")
    
    stats = []
    
    for cluster in df[cluster_col].unique():
        cluster_data = df[df[cluster_col] == cluster]
        
        # Расчет центра кластера
        center_lat = cluster_data['lat'].mean()
        center_lon = cluster_data['lon'].mean()
        
        # Расчет радиуса (среднее расстояние до центра)
        from haversine import haversine, Unit
        distances = []
        for _, row in cluster_data.iterrows():
            dist = haversine(
                (center_lat, center_lon),
                (row['lat'], row['lon']),
                unit=Unit.KILOMETERS
            )
            distances.append(dist)
        
        radius = sum(distances) / len(distances) if distances else 0
        
        stats.append({
            'cluster_id': cluster,
            'size': len(cluster_data),
            'center_lat': center_lat,
            'center_lon': center_lon,
            'radius_km': radius
        })
    
    return pd.DataFrame(stats)


def optimize_clusters(
    df: pd.DataFrame,
    min_clusters: int = 2,
    max_clusters: int = 20,
    lat_col: str = 'lat',
    lon_col: str = 'lon',
    random_state: int = 42
) -> dict:
    """
    Находит оптимальное количество кластеров с использованием локтевого метода.
    
    Parameters
    ----------
    df : pd.DataFrame
        Датафрейм с координатами
    min_clusters : int, default=2
        Минимальное количество кластеров
    max_clusters : int, default=20
        Максимальное количество кластеров
    lat_col : str, default='lat'
        Название колонки с широтой
    lon_col : str, default='lon'
        Название колонки с долготой
    random_state : int, default=42
        Seed для воспроизводимости
    
    Returns
    -------
    dict
        Словарь с результатами: инерция для каждого k
    """
    coords = df[[lat_col, lon_col]].values
    inertias = []
    k_range = range(min_clusters, max_clusters + 1)
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        kmeans.fit(coords)
        inertias.append(kmeans.inertia_)
    
    return {
        'k_values': list(k_range),
        'inertias': inertias
    }