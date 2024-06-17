# -*- coding: utf-8 -*-
import json
import os
import shutil
import subprocess
import zipfile
from datetime import datetime

import logging
from logging.handlers import RotatingFileHandler
import os
from pprint import pprint


def configure_logging(work_dir, log_filename="app"):
    log_folder = os.path.join(work_dir, 'Логи')
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    log_file_path = os.path.join(log_folder, f"{log_filename}.log")

    logger = logging.getLogger(log_filename)
    logger.setLevel(logging.INFO)

    # Проверяем, не добавлен ли уже обработчик к логгеру
    if not logger.handlers:
        handler = RotatingFileHandler(log_file_path, maxBytes=100000, backupCount=1, encoding='utf-8')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def extract_archive(input_archive, output_dir):
    """Использует 7z для распаковки архива в указанную директорию."""
    try:
        # Создаем выходную директорию, если она еще не существует
        os.makedirs(output_dir, exist_ok=True)
        # Запускаем 7z для извлечения архива
        subprocess.run(['7z', 'x', '-y', f'-o{output_dir}', input_archive], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при извлечении архива: {e}")
    except Exception as e:
        print(f"Общая ошибка: {e}")


def remove_file(filepath):
    """Удаляет файл по указанному пути."""
    try:
        os.remove(filepath)
    except OSError as e:
        print(f"Ошибка при удалении файла: {e}")


def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions


def archive_directories(work_dir, directories, archive_name):
    # Путь, куда будет сохранен общий архив (без указания расширения)
    archive_path = os.path.join(work_dir, archive_name)
    # Создаем временную директорию для архива
    temp_dir = os.path.join(work_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    # Копируем каждую директорию во временную папку
    for directory in directories:
        # Путь к папке, которую нужно скопировать во временную папку
        original_dir_path = os.path.join(work_dir, directory)
        temp_dir_path = os.path.join(temp_dir, directory)
        shutil.copytree(original_dir_path, temp_dir_path)

    # Создаем архив из временной папки
    shutil.make_archive(archive_path, 'zip', temp_dir)

    # Удалем временную папку
    shutil.rmtree(temp_dir)

    return f"{archive_path}.zip"


def clear_directories(work_dir):
    for folder_name in os.listdir(work_dir):
        folder_path = os.path.join(work_dir, folder_name)
        if os.path.isdir(folder_path) and folder_name not in ['Входящие', 'Исходящие', 'Логи']:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
    print("Папки очищены")


def synchronize_status_with_files(work_dir):
    status_file = os.path.join(work_dir, 'status.json')

    if not os.path.exists(status_file):
        return

    with open(status_file, 'r+', encoding="utf-8") as sf:
        status_data = json.load(sf)

        # Проверка существования файлов из status.json
        files_to_remove = []
        for filename, info in status_data.items():
            if not os.path.exists(info['filename']):
                files_to_remove.append(filename)

        for filename in files_to_remove:
            del status_data[filename]

        # Проверка существования файлов в папке "Входящие", которых нет в status.json
        incoming_folder = os.path.join(work_dir, 'Входящие')
        if os.path.exists(incoming_folder) and os.path.isdir(incoming_folder):
            for filename in os.listdir(incoming_folder):
                filepath = os.path.join(incoming_folder, filename)
                if os.path.isfile(filepath) and filename not in status_data:
                    # Добавление нового файла в status.json
                    status_data[filename] = {
                        "original_filename": filename,
                        "filename": filepath,
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                        "errors": 0,
                        "status": "Неизвестно",
                        "logs": ""
                    }

        # Перезапись обновленного status.json
        sf.seek(0)
        json.dump(status_data, sf, indent=4)
        sf.truncate()


def ensure_subfolders(directory, subfolders):
    # Проверяем, существует ли указанная папка
    if not os.path.exists(directory):
        print(f"Папка {directory} не существует.")
        return

    # Проверяем, пуста ли папка
    if not os.listdir(directory):  # Возвращает пустой список, если папка пуста
        print(f"Папка {directory} пуста. Создаем подпапки...")
        for folder in subfolders:
            new_folder_path = os.path.join(directory, folder)
            try:
                os.makedirs(new_folder_path)
                print(f"Подпапка {folder} создана.")
            except OSError as e:
                print(f"Невозможно создать подпапку {folder}: {e}")
    else:
        print(f"Папка {directory} не пуста.")
