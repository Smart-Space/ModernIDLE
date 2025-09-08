import sys
import subprocess
import threading


def run_script(filename):
    t = threading.Thread(target=_run_script, args=(filename,))
    t.daemon = True
    t.start()

def _run_script(filename):
    print("===Running script:", filename, '===')
    cmd = [sys.executable, '-u', filename]
    p = subprocess.Popen(cmd)
    p.wait()
    print("===Script finished:", filename, '===\n===exit code: ', p.returncode, '===\n')
