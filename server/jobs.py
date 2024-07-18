try:
    import yaml, subprocess, os, threading, time
    from pathlib import Path
    from modules.job_conf import JobConf
    from multiprocessing import Process, Queue
    from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
except ImportError as e:
    raise ImportError(f"Module import failed: {e}")

def create_file(file_path):
    fd = os.open(file_path, os.O_CREAT)
    os.close(fd)

def job_task(jobconf):
    if hasattr(jobconf, 'cmd') and jobconf.cmd:
        def initchild():
            if hasattr(jobconf, 'umask') and jobconf.umask:
                os.umask(jobconf.umask)
            if hasattr(jobconf, 'workingdir') and jobconf.workingdir:
                os.chdir(jobconf.workingdir)
            if hasattr(jobconf, 'stdout') and jobconf.stdout:
                stdout_fd = os.open(jobconf.stdout, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
                os.dup2(stdout_fd, 1)# Redirige la sortie du processus enfant vers le fichier
                os.close(stdout_fd)
            if hasattr(jobconf, 'stderr') and jobconf.stderr:
                stderr_fd = os.open(jobconf.stderr, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
                os.dup2(stderr_fd, 2)
                os.close(stderr_fd) 
        try:
            with subprocess.Popen(jobconf.cmd.split(), text=True, preexec_fn=initchild) as process:
                setattr(jobconf, 'process', process)
                setattr(jobconf, 'process', process.pid)
                setattr(jobconf, 'status', 'running')
                setattr(jobconf, 'status', 'completed' if process.returncode == 0 else 'failed')
                print(os.getpid())
        except OSError as e:
            print('OSError: ', e)
            setattr(jobconf, 'status','failed')
        finally:
            return jobconf

def monitoring_tasks(jobs_name, total_jobs):
    print('------------ Monitoring Call ------------- ')
    while True:
        for name in jobs_name:
            print(name)
            if total_jobs[name].status == 'stopped':
                total_jobs[name] = job_task(total_jobs[name])
            if total_jobs[name].process.poll() is None:
                print('Started')
            else:
                print('Stopped')
        time.sleep(5)

def run_jobs(jobs_name, total_jobs):
    monitoring = threading.Thread(target=monitoring_tasks, args=(jobs_name, total_jobs))
    monitoring.start()
    # subprocess.Popen(['/usr/bin/pwd'])
    # monitoring.join()
    # print('Total Jobs a la sortie\n', total_jobs['ping'])
    
    #if not_found:
    #    response = ', '.join(not_found) + ': job(s) not found.\n'
    #    clientsocket.sendall(bytes(response, 'utf-8'))

def init_jobs(data_received: str, clientsocket):
    actual_path = str(Path().resolve())
    fileconf_path = actual_path[0:actual_path.rfind('/')] + '/conf/conf.yml'
    fileconf_path = '/home/hkrifa/Bureau/taskmaster//conf/conf.yml'
    try:
        jobs_name = data_received.split()
        cmd = jobs_name.pop(0)
        with open(fileconf_path, 'r') as file:
            yaml_content = yaml.safe_load(file)
            total_jobs: dict = {}
            for jobname, conf in yaml_content.items():
                jobconf = JobConf(name=jobname, conf=conf)
                total_jobs[jobname] = jobconf
        run_jobs(jobs_name=jobs_name, total_jobs=total_jobs)
    except Exception as error:
        print(f'init_jobs: {error}')