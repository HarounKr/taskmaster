import time, subprocess

while True:
    subprocess.Popen(['cp', 'srcs/conf/conf.yml', '/tmp/'])
    time.sleep(3)