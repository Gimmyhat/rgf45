import subprocess
import sys
import traceback
import os
import psutil

def run(cmd, shell=False, wd=None, executable=None, wait=True, output=False):
    
    if isinstance(cmd,list):
        cmd = ';'.join(cmd)
    
    cmd = str(cmd)    
    print('Running :', cmd)
    
    if os.name=='nt':
        if not wait:
            subprocess.Popen(str(cmd), shell=shell, cwd=wd)
        else:    
            if output:
                out = subprocess.check_output(str(cmd), shell=shell, cwd=wd)
                out = out.decode('cp866')
                print(str(out))
                return out
            else:
                subprocess.check_call(cmd, shell=shell, cwd=wd)
    else:
        if shell:
            executable='/bin/bash'
        else:
            cmd = cmd.split(' ')
        if output:
            out = subprocess.check_output(cmd, shell=shell, cwd=wd, executable=executable)
            print(str(out))
            return out
        else:
            subprocess.check_call(cmd, shell=shell, cwd=wd, executable=executable)

def add_path(relpath):
    
    caller_path = traceback.extract_stack()[-2][0]
    #print caller_path
    path = os.path.abspath( os.path.dirname(caller_path) + '/' + relpath)
    #print path
    if path not in sys.path:
        sys.path.append( path )
    
def process_running(pid):

    if not psutil.pid_exists(pid):
        return False

    proc = psutil.Process(pid)

    return proc.status()!=psutil.STATUS_ZOMBIE