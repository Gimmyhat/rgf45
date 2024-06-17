# -*- coding: utf-8 -*-
# views.py
import shutil
import sys
from datetime import datetime
from math import ceil

from flask import Blueprint, request, render_template, current_app, send_from_directory, jsonify, g, send_file
import subprocess
import os
import threading
import json

import alt.cfg
from app.main.auth import auth
from app.utils.file_utils import (extract_archive, remove_file, allowed_file, archive_directories,
                                  clear_directories, configure_logging, synchronize_status_with_files,
                                  ensure_subfolders)
from app.utils.status_utils import update_status_file

main = Blueprint('main', __name__)
cfg = alt.cfg.read()


def run_script(script, cwd, filename):
    base_filename = os.path.splitext(filename)[0]
    logger = configure_logging(cwd, base_filename)

    print(f"Запуск скрипта: {script}")
    try:
        process = subprocess.Popen(['python', script], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, universal_newlines=True)
    except Exception as e:
        print(f"Ошибка при запуске скрипта {script}: {e}")
        return -1

    # Чтение вывода скрипта
    for line in process.stdout:
        logger.info(line.strip())

    process.stdout.close()
    return_code = process.wait()
    print("Фоновая задача завершена")

    return return_code


def run_scripts(scripts, cwd, filename):
    for script in scripts:
        return_code = run_script(script, cwd, filename)
        if return_code != 0:
            print(f"Ошибка при выполнении скрипта {script}. Останавливаем выполнение.")
            return return_code
    return 0


def background_task(scripts, cwd, filename):
    base_filename = os.path.splitext(filename)[0]

    # Запускаем первый скрипт и ждем его завершения
    return_code = run_scripts(scripts, cwd, filename)

    # Подсчет количества файлов в папке "Ошибки"
    errors_folder = os.path.join(cwd, 'Ошибки')
    if os.path.exists(errors_folder) and os.path.isdir(errors_folder):
        errors_count = len(
            [name for name in os.listdir(errors_folder) if os.path.isfile(os.path.join(errors_folder, name))])
    else:
        errors_count = 0

    # После выполнения создаем архив
    archive_name = base_filename[filename.find('_') + 1:] + '_xml'

    archive_file_dirs = [cfg.dir.send, cfg.dir.control]
    if errors_count:
        archive_file_dirs.append(cfg.dir.error)
    archive_file_path = archive_directories(cwd, archive_file_dirs, archive_name)
    archive_file_name = os.path.basename(archive_file_path)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    outgoing_filename = f"{timestamp}_{archive_file_name}"
    outgoing_folder = os.path.join(cwd, 'Исходящие')

    if not os.path.exists(outgoing_folder):
        os.makedirs(outgoing_folder)
    shutil.move(archive_file_path, os.path.join(outgoing_folder, outgoing_filename))

    # Обновляем статус обработки файла с добавлением пути к логу
    log_path = os.path.join('Логи', f"{base_filename}.log")

    # Завершаем обновление статуса, сообщая что процесс завершился
    finished_status = {"finished": True,
                       "archive": os.path.join('Исходящие', outgoing_filename),
                       "archive_filename": archive_file_name,
                       "errors": errors_count,
                       "logs": log_path,
                       }
    if return_code == 0:
        finished_status['status'] = "Успешно"
    else:
        finished_status['status'] = "Ошибка"

    update_status_file(cwd, filename, finished_status)

    # Очищаем папки, когда фоновая задача завершена и файл успешно обработан
    clear_directories(cwd)


@main.route('/', methods=['GET', 'POST'])
@main.route('/page/<int:page>', methods=['GET', 'POST'])
@auth.login_required
def upload_file(page=1):
    UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
    ALLOWED_EXTENSIONS = current_app.config['ALLOWED_EXTENSIONS']
    WORK_DIR = current_app.config['WORK_DIR']
    POSTS_PER_PAGE = current_app.config['POSTS_PER_PAGE']

    subfolders = list(cfg.dir.values()) + ['Логи', 'Входящие', 'Исходящие']
    ensure_subfolders(WORK_DIR, subfolders)

    synchronize_status_with_files(WORK_DIR)

    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
            file_timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            filename = file.filename
            historical_filename = f"{file_timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            print("Файл: ", filepath)
            try:
                file.save(filepath)
            except Exception as e:
                print(f"Не удалось сохранить файл: {e}")

            extract_archive(filepath, UPLOAD_FOLDER)
            incoming_folder = os.path.join(WORK_DIR, 'Входящие')
            if not os.path.exists(incoming_folder):
                os.makedirs(incoming_folder)
            shutil.copy(filepath, os.path.join(incoming_folder, historical_filename))
            remove_file(filepath)
            update_status_file(WORK_DIR, historical_filename, {
                "original_filename": filename,
                "filename": os.path.join(incoming_folder, historical_filename),
                "timestamp": timestamp,
                "errors": 0,
                "status": "В процессе",
                "logs": ""
            })

            script_1 = os.path.join(os.getcwd(), 'main.py')
            script_2 = os.path.join(os.getcwd(), 'xml_to_shp.py')

            thread_main = threading.Thread(target=background_task,
                                           args=((script_1, script_2), WORK_DIR, historical_filename))
            thread_main.start()

            return jsonify({'historical_filename': historical_filename})

        return jsonify({"error": "Неверный формат файла"}), 400

    files_status_paginated = {}
    total_pages = 0

    status_file = os.path.join(WORK_DIR, 'status.json')
    files_status = {}
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding="utf-8") as sf:
            files_status = json.load(sf)

        total_files_count = len(files_status)
        total_pages = ceil(total_files_count / POSTS_PER_PAGE)

        files_status_sorted = sorted(files_status.items(),
                                     key=lambda item: datetime.strptime(item[1]['timestamp'], "%Y-%m-%d %H:%M"),
                                     reverse=True)

        order_start = total_files_count
        for index, (_, details) in enumerate(files_status_sorted, start=1):
            details['order'] = order_start
            order_start -= 1

        start_index = (page - 1) * POSTS_PER_PAGE
        files_status_paginated = {
            filename: {
                **details,
                'order': total_files_count - (start_index + i)
            }
            for i, (filename, details) in enumerate(files_status_sorted[start_index:start_index + POSTS_PER_PAGE])
        }

    context = {
        'files_status': files_status_paginated,
        'can_view_logs': g.can_view_logs,
        'page': page,
        'total_pages': total_pages,
    }

    return render_template('index.html', **context)


@main.route('/download/<path:filename>', defaults={'extra_arg': None})
@main.route('/download/<path:filename>/<extra_arg>')
def download_file(filename, extra_arg):
    work_dir = current_app.config['WORK_DIR']
    status_file = os.path.join(work_dir, 'status.json')

    if os.path.exists(status_file):
        with open(status_file, 'r', encoding="utf-8") as sf:
            files_status = json.load(sf)

        filename = os.path.basename(filename)
        file_info = files_status.get(filename)

        if file_info and os.path.exists(file_info['filename']):
            if not extra_arg:
                return send_from_directory(directory=os.path.dirname(file_info['filename']),
                                           path=filename,
                                           as_attachment=True)
            else:
                filepath = os.path.join(work_dir, file_info[extra_arg])
                if extra_arg == 'logs':
                    sys.stderr.write("Файл: " + filepath + "\n")
                    sys.stderr.flush()
                    return send_file(filepath, mimetype='text/plain', as_attachment=False)
                else:
                    return send_from_directory(directory=os.path.dirname(filepath),
                                               path=os.path.basename(filepath),
                                               as_attachment=True)
    return "Файл не найден", 404


@main.route('/status/<filename>')
def get_status(filename):
    work_dir = current_app.config['WORK_DIR']
    status_file = os.path.join(work_dir, 'status.json')

    if os.path.exists(status_file):
        with open(status_file, 'r', encoding="utf-8") as sf:
            status_data = json.load(sf)
        file_status = status_data.get(filename, None)
        if file_status:
            return jsonify(file_status)

    return jsonify({"error": "Статус не найден"}), 404


@main.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    work_dir = current_app.config['WORK_DIR']
    # Удаление файла из директории и обновление status.json
    status_file = os.path.join(work_dir, 'status.json')

    if os.path.exists(status_file):
        with open(status_file, 'r+', encoding="utf-8") as sf:
            status_data = json.load(sf)
        if filename in status_data:
            file_info = status_data.pop(filename)  # Удалить информацию о файле из статуса
            sf.seek(0)
            json.dump(status_data, sf, indent=4)
            sf.truncate()

            # Удаление файла, если он существует
            file_path = file_info.get('filename')
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"message": "Файл удален"}), 200

    return jsonify({"error": "Файл не найден"}), 404
