import alt_path
import yaml
import os
from alt.dict_ import dict_


def project_dir():
    file_path = __file__.replace('\\', '/')
    main_pos = file_path.rfind('/main/')
    if main_pos == -1:
        raise Exception('Project dir not found')
    project_dir_ = file_path[:main_pos + 1]

    return project_dir_


def main_dir():
    return project_dir() + 'main/'


def projects_dir():
    file_path = __file__.replace('\\', '/')
    pos = file_path.rfind('/projects/')
    if pos == -1:
        raise Exception('Projects dir not found')
    projects_dir_ = file_path[:pos] + '/projects/'

    return projects_dir_


def user_projects_dir():
    projects_dir = os.path.abspath(project_dir() + '../').replace('\\', '/') + '/'

    return projects_dir


def root_dir():
    return os.path.abspath(projects_dir() + '..').replace('\\', '/') + '/'


def read_cfg_iter(cfg):
    for key, value in cfg.items():
        if isinstance(value, dict):
            read_cfg_iter(value)
        if isinstance(value, str):
            if value.startswith('<') and value.endswith('>'):
                file, field = value[1:-1].split(':')
                ext_cfg = read(file)
                cfg[key] = ext_cfg.get_(field)


def read(cfg_name='_main'):
    if '~' in cfg_name:
        cfg_name = os.path.expanduser(cfg_name)

    if os.path.exists(cfg_name):
        cfg_file = cfg_name
    else:
        cfg_file = main_dir() + '_cfg/' + cfg_name + '.cfg'

    uniq_cfg_file = cfg_file.replace('.cfg', '__uniq.cfg')
    if not os.path.exists(cfg_file) and not os.path.exists(uniq_cfg_file):
        raise Exception('Cfg file not exists', cfg_name)

    cfg = dict_()
    if os.path.exists(cfg_file):
        with open(cfg_file, encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
            if cfg is None:
                cfg = dict_()

    if os.path.exists(uniq_cfg_file):
        with open(uniq_cfg_file, encoding='utf-8') as f:
            host_cfg = yaml.safe_load(f)
            if host_cfg is not None:
                cfg.update(host_cfg)

    read_cfg_iter(cfg)

    return dict_(cfg)


def read_include_iter(cfg):
    for key, value in cfg.items():
        if isinstance(value, dict):
            read_include_iter(value)
            continue
        if isinstance(value, str):
            if value[0] == '<' and value[-1] == '>':
                cfg_name, attr = value[1:-1].split(':')
                cfg[key] = dict_(read(cfg_name)).get_(attr)


def read_global(cfg_name):
    cfg_file = user_projects_dir() + '_cfg/' + cfg_name + '.cfg'

    return read(cfg_file)


def host():
    host_cfg_file = project_dir() + '../_cfg/host.cfg'
    with open(host_cfg_file) as f:
        cfg = yaml.safe_load(f)

    return cfg['name']


def user():
    return read_global('user').name


def rep():
    s = main_dir().split('/')
    rep = s[-4]

    if rep == 'projects':
        rep = '_local'

    return rep


def project():
    s = main_dir().split('/')

    return s[-3]


def app():
    return user() + '-' + rep() + '-' + project()
