import os
import json
from src.core.processor import process_document


def process_folder(input_folder: str, output_folder: str):
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)

        if not filename.lower().endswith(
            ('.docx', '.pdf', '.jpeg', '.jpg', '.png', '.tiff', '.bmp')
        ):
            continue

        print(f"Обрабатываю файл: {filename}")

        result = process_document(file_path)

        output_file = os.path.join(
            output_folder,
            f"{os.path.splitext(filename)[0]}.json"
        )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        print(f"Сохранено: {output_file}")

