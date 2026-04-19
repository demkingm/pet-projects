"""Конфигурация приложения"""
import os
from pathlib import Path

import os
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
UPLOADS_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"

# Создаём папки
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Параметры модели
MODEL_PATH = str(MODELS_DIR / "calendar_model_best.pt")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE", "0.25"))
CROP_MARGIN = float(os.getenv("CROP_MARGIN", "0.1"))
CROP_SCALE = int(os.getenv("CROP_SCALE", "2"))

# Параметры OCR
OCR_LANG = os.getenv("OCR_LANG", "eng")
OCR_PSM = os.getenv("OCR_PSM", "7")
OCR_WHITELIST = os.getenv("OCR_WHITELIST", "0123456789")

# Настройки сервера
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))