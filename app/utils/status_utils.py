# status_utils.py

import json
import os


def read_status_file(work_dir):
    status_file = os.path.join(work_dir, 'status.json')
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as sf:
            return json.load(sf)
    return {}


def write_status_file(work_dir, status_data):
    status_file = os.path.join(work_dir, 'status.json')
    with open(status_file, 'w', encoding='utf-8') as sf:
        json.dump(status_data, sf, indent=4, ensure_ascii=False)


def update_status_file(work_dir, filename, updates):
    status_data = read_status_file(work_dir)
    status_data[filename] = status_data.get(filename, {})
    status_data[filename].update(updates)
    write_status_file(work_dir, status_data)
