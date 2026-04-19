import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from app_config import MODEL_PATH, CONFIDENCE_THRESHOLD, CROP_MARGIN, CROP_SCALE

class YOLODetector:
    """
    Класс для обнаружения и вырезания календарей на фото
    """
    def __init__(self):
        """Загружает модель YOLO"""
        print(f"Загрузка модели из {MODEL_PATH}")
        self.model = YOLO(MODEL_PATH)
        print("Модель загружена")

    def detect_and_crop(self, image_bytes: bytes):
        """Обнаруживает календари на изображении и вырезает их"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return None, None

        h, w = img.shape[:2]

        # 2. Запускаем детекцию
        results = self.model(img, conf=CONFIDENCE_THRESHOLD)

        # 3. Ищем самый большой прямоугольник (календарь)
        best_box = None
        best_area = 0

        for result in results:
            if result.boxes is not None:
                for box in result.boxes.xyxy.cpu().numpy():
                    x1, y1, x2, y2 = map(int, box)
                    area = (x2 - x1) * (y2 - y1)
                    if area > best_area:
                        best_area = area
                        best_box = (x1, y1, x2, y2)

        if best_box is None:
            return None, None

        x1, y1, x2, y2 = best_box

        # 4. Добавляем отступы (чтобы не обрезать цифры)
        margin_x = int((x2 - x1) * CROP_MARGIN)
        margin_y = int((y2 - y1) * CROP_MARGIN)

        x1 = max(0, x1 - margin_x)
        y1 = max(0, y1 - margin_y)
        x2 = min(w, x2 + margin_x)
        y2 = min(h, y2 + margin_y)

        # 5. Вырезаем область
        cropped = img[y1:y2, x1:x2]

        # 6. Увеличиваем размер (для лучшего OCR)
        scale = CROP_SCALE
        new_w = cropped.shape[1] * scale
        new_h = cropped.shape[0] * scale
        cropped = cv2.resize(cropped, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

        # 7. Преобразуем обратно в байты
        _, encoded = cv2.imencode('.jpg', cropped)

        return encoded.tobytes(), best_box    