# Calendar Renamer

Автономное приложение для распознавания номеров на календарях и переименования файлов.

## 🚀 Возможности

- Детекция календаря на фото с помощью YOLO
- Распознавание цифр с помощью EasyOCR
- Переименование файлов по распознанным номерам
- REST API для интеграции
- Docker контейнеризация
- Полная автономность (без интернета)

## 📋 Требования

- Python 3.10+
- EasyOCR
- 4GB RAM (рекомендуется 8GB)
- 2GB свободного места на диске

## 🔧 Установка

### Локальная установка

```bash
# Клонируйте репозиторий
git clone https://github.com/demkingm/pet-projects
cd calendar-renamer

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt

# Поместите модель в папку models/
cp /path/to/your/digit_detector.pt models/