import os
from dotenv import load_dotenv
from _libs.alt import cfg

load_dotenv()

cfg = cfg.read("_main__uniq")

DOCKER = os.getenv('DOCKER', False)


class DefaultConfig(object):
    # Значения по умолчанию
    if DOCKER:
        WORK_DIR = cfg.wd_docker.path
    else:
        WORK_DIR = cfg.wd.path

    UPLOAD_FOLDER = os.path.join(WORK_DIR, cfg.dir.shapes)
    OUTPUT_FOLDER = os.path.join(WORK_DIR, cfg.dir.send)
    ALLOWED_EXTENSIONS = set(['7z', 'zip', 'rar'])
    POSTS_PER_PAGE = 10
    DEBUG = True
