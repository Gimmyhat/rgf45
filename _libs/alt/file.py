import shutil
import os
import glob
import re
import sys
import platform
import ctypes
import pickle
import alt.cfg
import alt.system
import builtins

def slash(path):

    return path.replace('\\','/')

def touch(filename):

    mkdir( dir(filename) )
    open(filename,'w').close()

def name_ext(filename):
    
    filename = slash(filename)
    pos0 = filename.rfind('/')+1

    return filename[pos0:]

def ext(filename):
    
    filename = slash(filename)
    pos0 = filename.rfind('/')+1
    pos1 = filename.rfind('.')
    if pos1==-1 or pos1<pos0:
        return ''

    return filename[pos1+1:]
        
def name(filename):
    
    filename = slash(filename)
    if isdir(filename):
        filename = filename[:-1]
    pos0 = filename.rfind('/')+1
    pos1 = filename.rfind('.')
    if pos1==-1 or pos1<pos0:
        pos1 = len(filename)

    return filename[pos0:pos1]        
    
def isdir(name):
    
    if name[-1]=='\\' or name[-1]=='/':
        return True
    else:
        return False

def dir(filename):

    return os.path.dirname(filename) + '/'

def abspath(path):

    if isdir(path):
        return slash(os.path.abspath(path)) + '/'
    else:
        return slash(os.path.abspath(path))

def erase_dir(directory, exclude=[]):

    if not isdir(directory):
        raise Exception('Arg is not a directory')
    for root, dirs, files in os.walk(directory, topdown=False):
        for file in files:
            if file in exclude:
                continue
            os.remove(os.path.join(root,file))
        for dir in dirs:
            os.rmdir(os.path.join(root,dir))

def prepare_src_dest(src, dest):

    if isinstance(src, str) and re.search(r'[*?]', src) and isdir(dest):
        src_list = glob.glob(src)
        dest_list = [dest + os.path.basename(src_file) for src_file in src_list]
        return src_list, dest_list

    if isinstance(src, str) and isdir(dest):
        return [src], [dest + os.path.basename(src)]

    if isinstance(src, str) and isinstance(dest, str):
        return [src], [dest]

    if isinstance(src, list) and isinstance(dest, list):
        if len(src)!=len(dest):
            raise Exception('Src and Dest lists has different length ')
        return src, dest

    raise Exception('Unknown copy/move mode')

def copy(src, dest, overwrite=True, mkdir=True, move=False):

    src_list, dest_list = prepare_src_dest(src, dest)

    for src_file, dest_file in builtins.zip(src_list, dest_list):
        if not overwrite and os.path.exists(dest_file):
            continue
        if mkdir and not os.path.exists(os.path.dirname(dest_file)):
            sys.modules[__name__].mkdir(dir(dest_file))
        print('Copying', src_file, dest_file)
        if move:
            shutil.move(src_file, dest_file)
        else:
            shutil.copy2( src_file, dest_file + '~')
            shutil.move( dest_file + '~', dest_file)

def move(src, dest, overwrite=True, mkdir=True):

    copy(src, dest, overwrite=overwrite, mkdir=mkdir, move=True)

def mkdir(dir):

    if dir=='':
        return
    if not os.path.exists(dir):
        os.makedirs(dir)

def delete(mask, ignore=False):

    if isdir(mask) or os.path.isdir(mask):
        if not os.path.exists(mask):
            return
        try:
            shutil.rmtree(mask)
        except Exception:
            if ignore:
                print('Can not delete ' + mask)
            else:
                raise
    else:
        for file in glob.glob(mask):
            try:
                os.remove(file)
            except Exception:
                if ignore:
                    print('Can not delete ' + mask)
                else:
                    raise

def size(path):

    if isdir(path) or os.path.isdir(path):
        sz = 0
        for root, dirs, files in os.walk(path):
            for file in files:
                sz += os.stat(root + '/' + file).st_size
    else:
        sz = os.stat(path).st_size

    return sz

def free_space(folder):

    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        free = free_bytes.value
    else:
        st = os.statvfs(folder)
        free = st.f_bavail * st.f_frsize

    return int(free)

def read(filename):
    
    with open(filename, encoding='utf-8') as f:
        return f.read()

def write(filename, text):
    
    if isinstance(text, list):
        text = '\n'.join(text)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    
def readlines(filename):

    return read(filename).split('\n')

def wd():

    return slash(os.getcwd()) + '/'

def pkl_save(filename, data, mkdir_=False):

    print('Save', filename)

    if mkdir_:
        dir_ = os.path.dirname(filename)
        mkdir(dir_)

    with open(filename,'wb') as f:
        pickle.dump(data, f)

def pkl_load(filename):

    print('Load', filename)

    with open(filename,'rb') as f:
        data = pickle.load(f)

    return data

def zip(zip_file, include):

    if isinstance(include, list):
        include = ' '.join(include)
    if os.name=='nt':
        cmd = alt.cfg.root_dir() + 'tools/7-zip/7z a -bd %s %s'
    else:
        cmd = '7z a %s %s'
    alt.system.run(cmd % (zip_file, include))

def unzip(zip_file, dest='.', include=''):

    if isinstance(include, list):
        include = ' '.join(include)
    if os.name=='nt':
        zip_exe = alt.cfg.root_dir() + 'tools/7-Zip/7z.exe'
    else:
        zip_exe = '7z'
    cmd = '%s e -r -y -o%s %s %s' % (zip_exe, dest, zip_file, include)
    alt.system.run(cmd)

def dir_size(dir):

    sz = 0
    for root, dirs, files in os.walk(dir):
        for file_ in files:
            sz += os.stat(os.path.join(root,file_)).st_size

    return sz

def date_dir(date):

    return date[:4] + '/' + date + '/'
