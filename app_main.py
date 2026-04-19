import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from app_config import UPLOADS_DIR, RESULTS_DIR, HOST, PORT
from app_det_crop import YOLODetector
from app_easyocr import EasyOCRRecognizer as NumberRecognizer

# Создаём приложение
app = FastAPI(
    title="Calendar Recognition API",
    description="Детектирует календарь и распознаёт номер на фото",
    version="2.0.0"
)

# Инициализируем компоненты (загружаются один раз при старте)
detector = YOLODetector()
recognizer = NumberRecognizer()

# Модели ответов
class RecognitionResponse(BaseModel):
    success: bool
    number: Optional[str] = None
    message: str
    original_filename: str
    suggested_filename: Optional[str] = None


class RenameResponse(BaseModel):
    success: bool
    original_name: str
    new_name: Optional[str] = None
    number: Optional[str] = None
    message: str


# ============= ЭНДПОИНТЫ =============

@app.get("/health")
async def health_check():
    """Проверка работоспособности"""
    return {"status": "healthy", "model_loaded": True, "ocr_ready": True}


@app.post("/recognize", response_model=RecognitionResponse)
async def recognize_calendar(file: UploadFile = File(...)):
    """
    Распознаёт номер календаря на фото
    """
    try:
        contents = await file.read()
        cropped, box = detector.detect_and_crop(contents)

        if cropped is None:
            return RecognitionResponse(
                success=False,
                number=None,
                message="Календарь не найден на фото",
                original_filename=file.filename,
                suggested_filename=None
            )

        number = recognizer.extract_number(cropped)

        if number is None:
            return RecognitionResponse(
                success=False,
                number=None,
                message="Не удалось распознать номер на календаре",
                original_filename=file.filename,
                suggested_filename=None
            )

        return RecognitionResponse(
            success=True,
            number=number,
            message=f"Распознан номер: {number}",
            original_filename=file.filename,
            suggested_filename=f"{number}.jpg"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rename", response_model=RenameResponse)
async def rename_calendar_file(file: UploadFile = File(...)):
    """
    Распознаёт номер и возвращает предложение по переименованию
    """
    try:
        contents = await file.read()
        cropped, box = detector.detect_and_crop(contents)

        if cropped is None:
            return RenameResponse(
                success=False,
                original_name=file.filename,
                new_name=None,
                number=None,
                message="Календарь не найден на фото"
            )

        number = recognizer.extract_number(cropped)

        if number is None:
            return RenameResponse(
                success=False,
                original_name=file.filename,
                new_name=None,
                number=None,
                message="Не удалось распознать номер"
            )

        new_name = f"{number}.jpg"

        return RenameResponse(
            success=True,
            original_name=file.filename,
            new_name=new_name,
            number=number,
            message=f"Файл можно переименовать в {new_name}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rename-file")
async def rename_and_save(
    file: UploadFile = File(...),
    output_folder: str = None
):
    """
    Распознаёт номер и СОХРАНЯЕТ файл с новым именем
    """
    try:
        contents = await file.read()
        cropped, box = detector.detect_and_crop(contents)

        if cropped is None:
            return JSONResponse(
                status_code=404,
                content={"error": "Календарь не найден на фото"}
            )

        number = recognizer.extract_number(cropped)

        if number is None:
            return JSONResponse(
                status_code=404,
                content={"error": "Не удалось распознать номер"}
            )

        # Определяем папку для сохранения
        if output_folder:
            save_dir = Path(output_folder)
        else:
            save_dir = RESULTS_DIR

        save_dir.mkdir(parents=True, exist_ok=True)

        # Сохраняем файл с новым именем
        new_filename = f"{number}.jpg"
        save_path = save_dir / new_filename

        # Сохраняем оригинальный файл
        with open(save_path, "wb") as f:
            f.write(contents)

        return {
            "success": True,
            "original_name": file.filename,
            "new_name": new_filename,
            "number": number,
            "saved_path": str(save_path)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch")
async def batch_process(files: List[UploadFile] = File(...)):
    """
    Пакетная обработка нескольких фото
    """
    results = []
    for file in files:
        contents = await file.read()
        cropped, _ = detector.detect_and_crop(contents)

        if cropped is None:
            results.append({
                "filename": file.filename,
                "success": False,
                "number": None,
                "error": "Календарь не найден"
            })
            continue

        number = recognizer.extract_number(cropped)

        results.append({
            "filename": file.filename,
            "success": number is not None,
            "number": number,
            "error": None if number else "Номер не распознан"
        })

    return {"total": len(files), "results": results}


# ============= ЗАПУСК =============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)