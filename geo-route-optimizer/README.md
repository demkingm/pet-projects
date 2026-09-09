# 🗺️ Geo Route Optimizer

Оптимизация маршрутов для менеджеров с учетом географической близости и ограничений по времени.

## 📋 Описание проекта

Проект предназначен для автоматического распределения географических точек между менеджерами с учетом:
- **Географической близости** (кластеризация точек)
- **Равномерной нагрузки** (≤ 10 точек в день на менеджера)
- **22 рабочих дня**
- **3 менеджера**

### Результат работы
- Маршрут для каждого менеджера по дням
- Интерактивная карта с маршрутами
- Сводные таблицы для анализа нагрузки
- CSV файлы для дальнейшей работы

## 🚀 Быстрый старт

### Установка

```bash
# Клонирование репозитория
git clone https://github.com/demkingm/pet-projects.git
cd pet-projects/geo-route-optimizer

# Установка зависимостей
pip install -r requirements.txt
В корне проекта создать папку data и вложить в него .csv файл с наименованием data.

## Запуск 
python run.py


geo-route-optimizer/
├── src/
│   ├── __init__.py          # Инициализация пакета
│   ├── clustering.py         # Кластеризация точек
│   ├── routing.py            # Маршрутизация и распределение
│   └── visualize.py          # Визуализация результатов
├── data/
│   └── data.csv              # Исходные данные

├── run.py                    # Главный скрипт
├── requirements.txt          # Зависимости
└── README.md                 # Документация

📊 Формат входных данных
Файл data/data.csv должен содержать следующие колонки:


Колонка	  Тип	Описание	                      Пример
point_id	str	Уникальный идентификатор точки	ID1, ID2, ...
lat	      float	Широта (десятичные градусы)	  55.371884
lon	      float	Долгота (десятичные градусы)	43.846878
manager	  int	Номер менеджера                 (0, 1, 2)	0
n_visits	int	Количество посещений за месяц	  1

📝 Пример использования

import pandas as pd
from src.clustering import cluster_points
from src.routing import create_route_simple
from src.visualize import create_map

# Загрузка данных
df = pd.read_csv('data/data.csv')

# Создание маршрута
route = create_route_simple(df, max_points_per_day=10, n_managers=3)

# Визуализация
fig = create_map(route, color_by='manager')
fig.show()
