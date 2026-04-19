import easyocr
import cv2
import numpy as np
import io
from PIL import Image

class EasyOCRRecognizer:
    def __init__(self):
        # Инициализируем EasyOCR (только цифры)
        self.reader = easyocr.Reader(['en'], gpu=False)
        print("✅ EasyOCR инициализирован")

    def preprocess_image(self, image_bytes: bytes):
        """Предобработка изображения"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Увеличиваем размер
        scale = 3
        new_w = img.shape[1] * scale
        new_h = img.shape[0] * scale
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
        # Оттенки серого
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Повышение контраста
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        return gray

    def extract_number(self, image_bytes: bytes) -> str | None:
        """Извлекает номер из изображения"""
        try:
            processed = self.preprocess_image(image_bytes)
            
            # EasyOCR распознаёт только цифры
            results = self.reader.readtext(processed, allowlist='0123456789')
            
            if not results:
                return None
            
            # Собираем все найденные цифры
            all_digits = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # только уверенные результаты
                    all_digits.append(text)
            
            if not all_digits:
                return None
            
            # Объединяем все цифры
            number = ''.join(all_digits)
            
            # Если получилось 2-4 цифры, возвращаем
            if 2 <= len(number) <= 4:
                return number
            
            return None
            
        except Exception as e:
            print(f"EasyOCR ошибка: {e}")
            return None


# Для тестирования
if __name__ == "__main__":
    recognizer = EasyOCRRecognizer()
    
    # Тестируем на вырезанном календаре
    with open("test_cropped.jpg", "rb") as f:
        number = recognizer.extract_number(f.read())
    
    print(f"Распознанный номер: {number}")