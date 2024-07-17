try:
    import yaml, subprocess, os, threading, time
    from pathlib import Path
    from modules.job_conf import JobConf
    from multiprocessing import Process, Queue,Manager
    from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
except ImportError as e:
    raise ImportError(f"Module import failed: {e}")

def create_file(file_path):
    fd = os.open(file_path, os.O_CREAT)
    os.close(fd)

def job_task(jobconf):
    stdout_file = subprocess.PIPE
    stderr_file = subprocess.PIPE
    if hasattr(jobconf, 'cmd') and jobconf.cmd:
        try:
            if hasattr(jobconf, 'workingdir') and jobconf.workingdir:
                os.chdir(jobconf.workingdir)
                # print(os.getcwd())
            if hasattr(jobconf, 'umask') and jobconf.umask:
                # print('umask: ', jobconf.umask)
                os.umask(jobconf.umask)
            if hasattr(jobconf, 'stdout') and jobconf.stdout:
                create_file(file_path=jobconf.stdout)
                stdout_file = open(jobconf.stdout, 'a')
            if hasattr(jobconf, 'stderr') and jobconf.stderr:
                create_file(file_path=jobconf.stderr)
                stderr_file = open(jobconf.stderr, 'a')
            with subprocess.Popen(jobconf.cmd.split(), stdout=stdout_file, stderr=stderr_file, text=True) as process:
                print('here')
                setattr(jobconf, 'pid', process.pid)
                setattr(jobconf, 'status', 'running')
                setattr(jobconf, 'status', 'completed' if process.returncode == 0 else 'failed')
                setattr(jobconf, 'returncode', process.returncode)
                setattr(jobconf, 'process', process) 
                print(os.getpid())
        except OSError as e:
            print('OSError: ', e)
            setattr(jobconf, 'status','failed')
        finally:
            if stdout_file:
                stdout_file.close()
            if stderr_file:
                stderr_file.close()
            return jobconf

def monitoring_task(jobs_name, total_jobs):
    print('------------ Monitoring Call ------------- ')
    while True:
        for name in jobs_name:
            print(total_jobs[name])
            if total_jobs[name].process.poll() is None:
                print('Started')
            else:
                print('stopped')
        time.sleep(5)

def run_jobs(jobs_name, total_jobs):
    futures = {}
    names = list(total_jobs.keys())
    
    def when_done(future):
        try:
            result = future.result()
            future_name = result.name
            total_jobs[future_name] = result
        except Exception as e:
            print(f"Job generated an exception: {e}")
    with ThreadPoolExecutor() as executor:
        # while True:
        for name in jobs_name:
            if name in names:
                print('toto')
                if total_jobs[name].status == 'stopped':
                    future = executor.submit(job_task, total_jobs[name])
                    future.add_done_callback(when_done)
    monitoring = threading.Thread(target=monitoring_task, args=(jobs_name, total_jobs))
    monitoring.start()
    # subprocess.Popen(['/usr/bin/pwd'])
    # monitoring.join()
    # print('Total Jobs a la sortie\n', total_jobs['ping'])
    
    #if not_found:
    #    response = ', '.join(not_found) + ': job(s) not found.\n'
    #    clientsocket.sendall(bytes(response, 'utf-8'))

def init_jobs(data_received: str, clientsocket):
    # actual_path = str(Path().resolve())
    # fileconf_path = actual_path[0:actual_path.rfind('/')] + '/conf/conf.yml'
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