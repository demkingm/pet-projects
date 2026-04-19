
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
from pathlib import Path

from app_config import OCR_LANG, OCR_PSM, OCR_WHITELIST



class NumberRecognizer:
    """
    Класс для распознавания цифр с вырезанных календарей
    """
    
    def __init__(self):
        """Инициализация OCR"""
        self.config = f'--oem 1 --psm {OCR_PSM} -c tessedit_char_whitelist={OCR_WHITELIST}'
        print(f"✅ OCR инициализирован. Язык: {OCR_LANG}, PSM: {OCR_PSM}")
    
    def preprocess_image(self, image_bytes: bytes):
        """
        Предобработка изображения для улучшения распознавания
        """
        # Открываем изображение
        img = Image.open(io.BytesIO(image_bytes))
        
        # Увеличиваем в 2-3 раза
        scale = 2
        new_size = (img.width * scale, img.height * scale)
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Конвертируем в оттенки серого
        img = img.convert('L')
        
        # Повышаем контраст
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # Повышаем резкость
        img = img.filter(ImageFilter.SHARPEN)
        
        return img
    
    def extract_number(self, image_bytes: bytes) -> str | None:
        """
        Извлекает номер из вырезанного календаря
        """
        # try:
        #     # Предобработка
        #     processed_img = self.preprocess_image(image_bytes)
            
        #     # Распознавание
        #     text = pytesseract.image_to_string(
        #         processed_img, 
        #         lang=OCR_LANG, 
        #         config=self.config
        #     )
            
        #     # Очищаем от мусора (оставляем только цифры)
        #     number = ''.join([c for c in text.strip() if c.isdigit()])
            
        #     return number if number else None
            
        # except Exception as e:
        #     print(f"OCR ошибка: {e}")
        #     return None

        try:
            processed = self.preprocess_image(image_bytes)
            configs = [
                r'--oem 1 --psm 8 -c tessedit_char_whitelist=0123456789',  # Одно слово
                r'--oem 1 --psm 6 -c tessedit_char_whitelist=0123456789',  # Блок текста
                r'--oem 1 --psm 13 -c tessedit_char_whitelist=0123456789', # Сырая строка
                r'--oem 1 --psm 7 -c tessedit_char_whitelist=0123456789',  # Одна строка
             ]
        
            best_number = None
            best_len = 0

            for config in configs:
                text = pytesseract.image_to_string(processed, lang=OCR_LANG, config=config)
                number = ''.join([c for c in text.strip() if c.isdigit()])
                
                if len(number) > best_len:
                    best_len = len(number)
                    best_number = number
                
                # Если нашли 2-4 цифры, возвращаем сразу
                if 2 <= len(number) <= 4:
                    return number
            
            return best_number if best_len >= 2 else None
        
        except Exception as e:
            print(f"OCR ошибка: {e}")
            return None
        
    
    def extract_number_from_file(self, image_path: str) -> str | None:
        """Извлекает номер из файла изображения"""
        with open(image_path, "rb") as f:
            return self.extract_number(f.read())