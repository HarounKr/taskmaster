from multiprocessing import Process, Lock
import os
import subprocess

def f(l, i):
    process = subprocess.Popen(['ping', '-c', '10', '8.8.8.8'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    print('Subprocess PID:', process.pid)
    print('Process PID', os.getpid())
    print(out.decode())


if __name__ == '__main__':
    lock = Lock()
    num = 1
    # for num in range(10):
    p = Process(target=f, args=(lock, num))
    p.start()
    p.join()
    print('ca ressort')