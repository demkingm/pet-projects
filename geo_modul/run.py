import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("="*60)
print("  ЗАПУСК МАРШРУТИЗАЦИИ")
print("="*60)

import pandas as pd
import numpy as np
from src.clustering import cluster_points

# Загрузка данных
data_path = os.path.join(project_root, 'data', 'data.csv')
df = pd.read_csv(data_path)

print(f"✅ Загружено {len(df)} точек")

# ============================================
# 1. ИСПОЛЬЗУЕМ ТОЛЬКО УНИКАЛЬНЫЕ ТОЧКИ (1 раз)
# ============================================
print("\n📌 Каждая точка посещается 1 раз в месяц")
print(f"   Всего посещений: {len(df)}")

# Берем только нужные колонки
df_work = df[['point_id', 'lat', 'lon']].copy()

# ============================================
# 2. КЛАСТЕРИЗАЦИЯ
# ============================================
print("\n🔄 Кластеризация...")
clustered = cluster_points(df_work, max_points_per_cluster=10)
print(f"   Создано {clustered['cluster_id'].nunique()} кластеров")

# ============================================
# 3. РАСПРЕДЕЛЕНИЕ ПО МЕНЕДЖЕРАМ (равномерно)
# ============================================
print("\n👤 Распределение по менеджерам...")
n_managers = 3
max_points_per_day = 10  # можно изменить на 12, если нужно

# Перемешиваем для равномерного распределения
clustered = clustered.sample(frac=1, random_state=42).reset_index(drop=True)
clustered['manager'] = [i % n_managers for i in range(len(clustered))]

# ============================================
# 4. РАСПРЕДЕЛЕНИЕ ПО ДНЯМ
# ============================================
print("\n📅 Распределение по дням...")
n_days = 22

# Сортируем по менеджеру и кластеру
clustered = clustered.sort_values(['manager', 'cluster_id'])
clustered['visit_day'] = -1

# Для каждого менеджера распределяем точки по дням
for manager in range(n_managers):
    manager_mask = clustered['manager'] == manager
    manager_indices = clustered[manager_mask].index
    n_points = len(manager_indices)
    
    # Расчет дней для этого менеджера
    days_needed = (n_points + max_points_per_day - 1) // max_points_per_day
    print(f"   Менеджер {manager}: {n_points} точек, {days_needed} дней")
    
    # Распределяем по дням
    day = 1
    count = 0
    
    for idx in manager_indices:
        clustered.loc[idx, 'visit_day'] = day
        count += 1
        
        if count >= max_points_per_day:
            day += 1
            count = 0

# ============================================
# 5. ПРОВЕРКА
# ============================================
max_day = clustered['visit_day'].max()
print(f"\n📅 Максимальный день: {max_day} (из {n_days})")

if max_day <= n_days:
    print(f"✅ Все дни в пределах {n_days}")
else:
    print(f"⚠️ ВНИМАНИЕ! Нужно {max_day} дней, а есть {n_days}")
    print(f"   Уменьшите max_points_per_day или добавьте менеджеров")

# ============================================
# 6. ПОРЯДОК В МАРШРУТЕ
# ============================================
print("\n🗺️ Расчет порядка в маршруте...")
clustered['order_in_route'] = -1

for manager in range(n_managers):
    for day in clustered[clustered['manager'] == manager]['visit_day'].unique():
        mask = (clustered['manager'] == manager) & (clustered['visit_day'] == day)
        day_indices = clustered[mask].index
        
        # Сортируем по кластеру
        day_data = clustered.loc[day_indices].sort_values('cluster_id')
        day_indices_sorted = day_data.index
        
        for order, idx in enumerate(day_indices_sorted):
            clustered.loc[idx, 'order_in_route'] = order

# ============================================
# 7. ФОРМИРУЕМ РЕЗУЛЬТАТ
# ============================================
route = clustered[['point_id', 'visit_day', 'cluster_id', 'order_in_route', 'manager']].copy()

# ============================================
# СТАТИСТИКА
# ============================================
print("\n" + "="*60)
print("  📊 СТАТИСТИКА")
print("="*60)

print(f"\n📌 Всего точек: {len(route)}")
print(f"📌 Всего дней: {route['visit_day'].nunique()}")
print(f"📌 Менеджеров: {n_managers}")
print(f"📌 Максимум точек в день на менеджера: {max_points_per_day}")

# По менеджерам
print("\n👤 По менеджерам:")
for manager in range(n_managers):
    count = len(route[route['manager'] == manager])
    days = route[route['manager'] == manager]['visit_day'].nunique()
    avg = count / days if days > 0 else 0
    print(f"   Менеджер {manager}: {count} точек, {days} дней, в среднем {avg:.1f} в день")

# Проверка по дням
day_stats = route.groupby(['manager', 'visit_day']).size().unstack(fill_value=0)
max_per_day = day_stats.max().max()

print(f"\n📊 Максимум точек у менеджера в день: {max_per_day}")

if max_per_day <= max_points_per_day:
    print(f"✅ Все в пределах лимита (≤ {max_points_per_day})")
else:
    print(f"⚠️ Есть превышение: {max_per_day} > {max_points_per_day}")

# ============================================
# ПОДРОБНЫЙ МАРШРУТ (первые дни)
# ============================================
print("\n" + "="*60)
# ============================================
# ПОДРОБНЫЙ МАРШРУТ (первые дни)
# ============================================
print("\n" + "="*60)
print("  📋 ПОДРОБНЫЙ МАРШРУТ (первые 3 дня)")
print("="*60)

# Объединяем с координатами
route_full = route.merge(
    df[['point_id', 'lat', 'lon']],
    on='point_id',
    how='left'
)

route_full = route_full.sort_values(['manager', 'visit_day', 'order_in_route'])

for manager in sorted(route_full['manager'].unique()):
    manager_data = route_full[route_full['manager'] == manager]
    
    print(f"\n{'='*60}")
    print(f"👤 МЕНЕДЖЕР {int(manager)}")
    print(f"{'='*60}")
    print(f"📊 Всего точек: {len(manager_data)}")
    print(f"📅 Дней: {manager_data['visit_day'].nunique()}")
    
    # Показываем первые 3 дня
    days_shown = 0
    for day in sorted(manager_data['visit_day'].unique()):
        if days_shown >= 3:
            print(f"\n  ... и еще {manager_data['visit_day'].nunique() - 3} дней")
            break
            
        day_data = manager_data[manager_data['visit_day'] == day]
        day_data = day_data.sort_values('order_in_route')
        
        print(f"\n  📅 ДЕНЬ {day} (точек: {len(day_data)})")
        print(f"  {'─'*65}")
        print(f"  {'№':<4} {'Точка':<12} {'Широта':<12} {'Долгота':<12} {'Кластер':<8}")
        print(f"  {'─'*65}")
        
        for _, row in day_data.iterrows():
            print(f"  {int(row['order_in_route'])+1:<4} "
                  f"{row['point_id']:<12} "
                  f"{row['lat']:<12.6f} "
                  f"{row['lon']:<12.6f} "
                  f"{int(row['cluster_id']):<8}")
        
        if len(day_data) > max_points_per_day:
            print(f"  ⚠️ ПРЕВЫШЕНИЕ! {len(day_data)} > {max_points_per_day}")
        else:
            print(f"  ✅ {len(day_data)}/{max_points_per_day}")
        
        days_shown += 1

# ============================================
# СВОДНАЯ ТАБЛИЦА ПО ДНЯМ
# ============================================
print("\n" + "="*60)
print("  📊 СВОДНАЯ ТАБЛИЦА ПО ДНЯМ")
print("="*60)

# Сводная таблица: менеджеры × дни
pivot_table = route.groupby(['manager', 'visit_day']).size().unstack(fill_value=0)

print("\nКоличество точек по дням и менеджерам:")
print(pivot_table.to_string())

# Проверяем заполненность дней
print(f"\n📊 Статистика по дням:")
for day in range(1, min(23, route['visit_day'].max() + 1)):
    day_total = len(route[route['visit_day'] == day])
    day_managers = route[route['visit_day'] == day]['manager'].nunique()
    print(f"   День {day:2d}: {day_total:3d} точек, {day_managers} менеджеров")

# ============================================
# ПРОВЕРКА: все ли точки учтены
# ============================================
print("\n" + "="*60)
print("  🔍 ПРОВЕРКА")
print("="*60)

# Проверяем, что все точки из исходного датафрейма есть в маршруте
all_points = set(df['point_id'])
routed_points = set(route['point_id'])
missing = all_points - routed_points

if len(missing) == 0:
    print("✅ Все точки включены в маршрут!")
else:
    print(f"⚠️ {len(missing)} точек не включены в маршрут:")
    print(f"   {list(missing)[:10]}")

# Проверяем дубликаты
duplicates = route[route.duplicated(subset=['point_id'], keep=False)]
if len(duplicates) == 0:
    print("✅ Нет дубликатов точек (каждая точка 1 раз)")
else:
    print(f"⚠️ Найдено {len(duplicates)} дубликатов")

# ============================================
# СОХРАНЕНИЕ РЕЗУЛЬТАТОВ
# ============================================
print("\n" + "="*60)
print("  💾 СОХРАНЕНИЕ")
print("="*60)

results_path = os.path.join(project_root, 'results')
os.makedirs(results_path, exist_ok=True)

# 1. Полный маршрут
route_full.to_csv(os.path.join(results_path, 'route_full.csv'), index=False)
print(f"✅ route_full.csv - полный маршрут")

# 2. Сводная таблица
pivot_table.to_csv(os.path.join(results_path, 'daily_summary.csv'))
print(f"✅ daily_summary.csv - сводная таблица")

# 3. Отдельно для каждого менеджера
for manager in sorted(route_full['manager'].unique()):
    manager_data = route_full[route_full['manager'] == manager]
    manager_data.to_csv(
        os.path.join(results_path, f'manager_{int(manager)}_route.csv'),
        index=False
    )
    print(f"✅ manager_{int(manager)}_route.csv")

# 4. Только список точек по дням (без координат)
route[['point_id', 'visit_day', 'manager', 'order_in_route']].to_csv(
    os.path.join(results_path, 'route_simple.csv'),
    index=False
)
print(f"✅ route_simple.csv - краткий маршрут")

# ============================================
# КАРТА
# ============================================
print("\n🗺️ Создание карты...")

try:
    import plotly.express as px
    
    fig = px.scatter_mapbox(
        route_full,
        lat='lat',
        lon='lon',
        color='manager',
        hover_name='point_id',
        hover_data={
            'visit_day': True,
            'cluster_id': True,
            'order_in_route': True,
            'lat': False,
            'lon': False
        },
        zoom=10,
        center=dict(lat=route_full['lat'].mean(), lon=route_full['lon'].mean()),
        title=f'Маршруты менеджеров ({len(route)} точек, {route["visit_day"].nunique()} дней)',
        height=700,
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        margin=dict(r=0, l=0, t=50, b=0)
    )
    
    map_path = os.path.join(results_path, 'map.html')
    fig.write_html(map_path)
    print(f"✅ map.html - интерактивная карта")
    
    # Открываем в браузере
    import webbrowser
    webbrowser.open(map_path)
    print("✅ Карта открыта в браузере")
    
except Exception as e:
    print(f"⚠️ Ошибка карты: {e}")

# ============================================
# ИТОГ
# ============================================
print("\n" + "="*60)
print("  ✅ ГОТОВО!")
print("="*60)

print(f"""
📊 ИТОГОВАЯ СТАТИСТИКА:
   • Всего точек: {len(route)}
   • Дней: {route['visit_day'].nunique()} (из 22)
   • Менеджеров: {n_managers}
   • Максимум в день на менеджера: {max_points_per_day}
   • Максимум в день (все менеджеры): {route.groupby('visit_day').size().max()}

📁 Результаты в папке: {results_path}
   • route_full.csv - полный маршрут с координатами
   • route_simple.csv - краткий маршрут
   • daily_summary.csv - сводная таблица
   • manager_X_route.csv - маршрут менеджера X
   • map.html - интерактивная карта
""")

print("="*60)