"""
Модуль визуализации для отображения результатов кластеризации и маршрутизации.

Содержит функции для создания интерактивных карт и статических графиков.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns


def create_map(
    df: pd.DataFrame,
    center_lat: float = 55.9,
    center_lon: float = 43.7,
    zoom: int = 10,
    color_by: str = 'manager',
    title: str = 'Распределение точек',
    height: int = 700
) -> Optional[go.Figure]:
    """
    Создает интерактивную карту с точками.
    
    Parameters
    ----------
    df : pd.DataFrame
        Датафрейм с колонками lat, lon и цветовой колонкой
    center_lat : float, default=55.9
        Широта центра карты
    center_lon : float, default=43.7
        Долгота центра карты
    zoom : int, default=10
        Уровень приближения
    color_by : str, default='manager'
        Колонка для раскраски точек
    title : str, default='Распределение точек'
        Заголовок карты
    height : int, default=700
        Высота карты в пикселях
    
    Returns
    -------
    go.Figure or None
        Объект Plotly Figure или None в случае ошибки
    
    Examples
    --------
    >>> fig = create_map(df, color_by='cluster_id', title='Кластеры')
    >>> fig.show()
    """
    if 'lat' not in df.columns or 'lon' not in df.columns:
        print("❌ Ошибка: требуются колонки 'lat' и 'lon'")
        return None
    
    if color_by not in df.columns:
        print(f"❌ Ошибка: колонка '{color_by}' не найдена")
        return None
    
    # Подготовка hover_data
    hover_data = {
        'lat': False,
        'lon': False,
    }
    
    for col in ['point_id', 'cluster_id', 'manager', 'visit_day', 'order_in_route']:
        if col in df.columns and col != color_by:
            hover_data[col] = True
    
    # Создание карты
    fig = px.scatter_mapbox(
        df,
        lat='lat',
        lon='lon',
        color=color_by,
        hover_name='point_id' if 'point_id' in df.columns else None,
        hover_data=hover_data,
        zoom=zoom,
        center=dict(lat=center_lat, lon=center_lon),
        title=title,
        height=height,
        color_continuous_scale='Viridis' if df[color_by].dtype in ['int64', 'float64'] else None
    )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        margin=dict(r=0, l=0, t=50, b=0),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    
    return fig


def create_simple_scatter(
    df: pd.DataFrame,
    color_by: str = 'manager',
    title: str = 'Распределение точек'
) -> go.Figure:
    """
    Создает простой scatter plot (не требует интернета).
    
    Parameters
    ----------
    df : pd.DataFrame
        Датафрейм с колонками lat, lon
    color_by : str, default='manager'
        Колонка для раскраски
    title : str, default='Распределение точек'
        Заголовок
    
    Returns
    -------
    go.Figure
        Объект Plotly Figure
    """
    if color_by not in df.columns:
        color_by = None
    
    fig = px.scatter(
        df,
        x='lon',
        y='lat',
        color=color_by,
        hover_name='point_id' if 'point_id' in df.columns else None,
        title=title,
        labels={'lon': 'Долгота', 'lat': 'Широта'},
        height=700
    )
    
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig


def plot_cluster_statistics(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (14, 5)
) -> None:
    """
    Создает графики со статистикой кластеров.
    
    Parameters
    ----------
    df : pd.DataFrame
        Датафрейм с колонками 'cluster_id' и координатами
    save_path : str, optional
        Путь для сохранения графика
    figsize : Tuple[int, int], default=(14, 5)
        Размер фигуры
    
    Examples
    --------
    >>> plot_cluster_statistics(df, save_path='cluster_stats.png')
    """
    if 'cluster_id' not in df.columns:
        print("❌ Ошибка: требуется колонка 'cluster_id'")
        return
    
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # 1. Размеры кластеров
    ax1 = axes[0]
    cluster_sizes = df['cluster_id'].value_counts().sort_index()
    bars = ax1.bar(cluster_sizes.index, cluster_sizes.values, 
                   color='skyblue', edgecolor='black')
    ax1.set_xlabel('Номер кластера')
    ax1.set_ylabel('Количество точек')
    ax1.set_title('Размеры кластеров')
    ax1.grid(True, alpha=0.3)
    
    # Добавляем значения на столбцы
    for bar, value in zip(bars, cluster_sizes.values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(value), ha='center', va='bottom', fontsize=10)
    
    # 2. Распределение по дням
    if 'visit_day' in df.columns and 'manager' in df.columns:
        ax2 = axes[1]
        pivot = df.groupby(['visit_day', 'manager']).size().unstack(fill_value=0)
        pivot.plot(kind='bar', ax=ax2, stacked=True, colormap='viridis', edgecolor='black')
        ax2.set_xlabel('День')
        ax2.set_ylabel('Количество точек')
        ax2.set_title('Распределение по дням и менеджерам')
        ax2.legend(title='Менеджер')
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ График сохранен как '{save_path}'")
    
    plt.show()


def create_route_animation(
    df: pd.DataFrame,
    save_path: Optional[str] = None
) -> Optional[go.Figure]:
    """
    Создает анимированную карту маршрутов по дням.
    
    Parameters
    ----------
    df : pd.DataFrame
        Датафрейм с колонками lat, lon, manager, visit_day
    save_path : str, optional
        Путь для сохранения HTML файла
    
    Returns
    -------
    go.Figure or None
        Объект Plotly Figure
    
    Examples
    --------
    >>> fig = create_route_animation(df)
    >>> fig.show()
    """
    required_cols = ['lat', 'lon', 'visit_day']
    for col in required_cols:
        if col not in df.columns:
            print(f"❌ Ошибка: требуется колонка '{col}'")
            return None
    
    df_anim = df.copy()
    df_anim['day_label'] = df_anim['visit_day'].apply(lambda x: f'День {x}')
    
    color_by = 'manager' if 'manager' in df.columns else None
    hover_name = 'point_id' if 'point_id' in df.columns else None
    
    fig = px.scatter_mapbox(
        df_anim,
        lat='lat',
        lon='lon',
        color=color_by,
        hover_name=hover_name,
        animation_frame='visit_day',
        title='Анимация маршрутов по дням',
        zoom=10,
        center=dict(lat=df['lat'].mean(), lon=df['lon'].mean()),
        height=700
    )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        margin=dict(r=0, l=0, t=50, b=0)
    )
    
    if save_path:
        fig.write_html(save_path)
        print(f"✅ Анимация сохранена как '{save_path}'")
    
    return fig


def create_comparison_map(
    df: pd.DataFrame,
    center_lat: float = 55.9,
    center_lon: float = 43.7,
    zoom: int = 10
) -> go.Figure:
    """
    Создает карту с разделением на подграфики для сравнения.
    
    Parameters
    ----------
    df : pd.DataFrame
        Датафрейм с колонками lat, lon, manager, cluster_id
    center_lat : float, default=55.9
        Широта центра
    center_lon : float, default=43.7
        Долгота центра
    zoom : int, default=10
        Уровень приближения
    
    Returns
    -------
    go.Figure
        Объект Plotly Figure с двумя картами
    """
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('По менеджерам', 'По кластерам'),
        specs=[[{'type': 'mapbox'}, {'type': 'mapbox'}]]
    )
    
    # Карта 1: По менеджерам
    for manager in df['manager'].unique():
        data = df[df['manager'] == manager]
        fig.add_trace(
            go.Scattermapbox(
                lat=data['lat'],
                lon=data['lon'],
                mode='markers',
                marker=dict(size=8, opacity=0.7),
                name=f'Менеджер {manager}',
                showlegend=True
            ),
            row=1, col=1
        )
    
    # Карта 2: По кластерам
    for cluster in df['cluster_id'].unique():
        data = df[df['cluster_id'] == cluster]
        fig.add_trace(
            go.Scattermapbox(
                lat=data['lat'],
                lon=data['lon'],
                mode='markers',
                marker=dict(size=8, opacity=0.7),
                name=f'Кластер {cluster}',
                showlegend=True
            ),
            row=1, col=2
        )
    
    # Настройка layout
    fig.update_layout(
        height=600,
        margin=dict(r=0, l=0, t=50, b=0)
    )
    
    # Настройка mapbox для обоих подграфиков
    for i in [1, 2]:
        fig.update_mapbox(
            style="carto-positron",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom,
            row=1, col=i
        )
    
    return fig