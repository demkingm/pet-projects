import requests
from pathlib import Path

API_URL = "http://localhost:8000"

def rename_all_photos(folder_path: str):
    """Переименовывает все фото в папке по распознанным номерам"""
    folder = Path(folder_path)
    photos = list(folder.glob("*.jpg")) + list(folder.glob("*.JPG"))
    
    print(f"📸 Найдено фото: {len(photos)}")
    print("=" * 50)
    
    renamed = 0
    failed = 0
    
    for photo in photos:
        print(f"\n📄 {photo.name}", end=" ")
        
        try:
            with open(photo, "rb") as f:
                response = requests.post(f"{API_URL}/rename", files={"file": f})
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    new_name = data["new_name"]
                    new_path = photo.parent / new_name
                    photo.rename(new_path)
                    print(f"✅ → {new_name}")
                    renamed += 1
                else:
                    print(f"❌ {data['message']}")
                    failed += 1
            else:
                print(f"❌ Ошибка сервера: {response.status_code}")
                failed += 1
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Статистика:")
    print(f"   ✅ Переименовано: {renamed}")
    print(f"   ❌ Не удалось: {failed}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        photos_folder = sys.argv[1]
    else:
        photos_folder =  r"C:\Users\grigr\Desktop\project_data_science\saffer\data"
    
    rename_all_photos(photos_folder)