try:
    import yaml, subprocess, os, threading, time, signal
    from pathlib import Path
    from modules.job_conf import JobConf
    from multiprocessing import Process, Queue
    from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor 
except ImportError as e:
    raise ImportError(f"Module import failed: {e}")

def create_file(file_path):
    fd = os.open(file_path, os.O_CREAT)
    os.close(fd)

def start_procs(numprocs: int, initchild, cmd) -> list:
    procs = []
    for i in range(0, numprocs):
        print('i :  ', i)
        process = subprocess.Popen(cmd.split(), text=True, preexec_fn=initchild)
        procs.append((process, 0))
    return procs

def job_task(jobconf):
    print(f"Monitoring process : {os.getpid()}")
    print('Name : ', jobconf.name)
    procs = []
    def kill_childs(signum, frame):
        print(f"Received signal {signum}. Terminating child processes...")
        for proc, retries in procs:
            if proc.poll() is None:
                os.kill(proc.pid, signum)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.kill(proc.pid, signal.SIGKILL)
        sys.exit(0)

    signal.signal(signal.SIGTERM, kill_childs)

    if hasattr(jobconf, 'cmd') and jobconf.cmd:
        def initchild():
            if hasattr(jobconf, 'umask') and jobconf.umask:
                os.umask(jobconf.umask)
            if hasattr(jobconf, 'workingdir') and jobconf.workingdir:
                os.chdir(jobconf.workingdir)
            if hasattr(jobconf, 'stdout') and jobconf.stdout:
                stdout_fd = os.open(jobconf.stdout, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
                os.dup2(stdout_fd, 1) # Redirige la sortie du processus enfant vers le fichier
                os.close(stdout_fd)
            if hasattr(jobconf, 'stderr') and jobconf.stderr:
                stderr_fd = os.open(jobconf.stderr, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
                os.dup2(stderr_fd, 2)
                os.close(stderr_fd)
        try:
            print('Number of procs : ', jobconf.numprocs)
            procs = start_procs(numprocs=jobconf.numprocs, initchild=initchild, cmd=jobconf.cmd)
            while True:
                new_procs = []
                for proc, retries in procs:
                    print(f"Process {proc.pid} is started with exit code {proc.returncode}")
                    if proc.poll() is not None:
                        print(f"Process {proc.pid} terminated with exit code {proc.returncode}")
                        print(jobconf.autorestart)
                        if proc.returncode not in jobconf.exitcodes and jobconf.autorestart == "unexpected":
                            if retries < jobconf.startretries:
                                print(f"Restarting process {proc.pid}. Attempt {retries + 1}")
                                new_process = subprocess.Popen(jobconf.cmd.split(), text=True, preexec_fn=initchild)
                                new_procs.append((new_process, retries + 1))
                            else:
                                print(f"Process {proc.pid} has exceeded the maximum retry.")
                        elif jobconf.autorestart is True:
                            new_process = subprocess.Popen(jobconf.cmd.split(), text=True, preexec_fn=initchild)
                            new_procs.append((new_process, 0))
                    else:
                        new_procs.append((proc, retries))
                    time.sleep(1)
                procs = new_procs
                if not procs:
                    break
        except OSError as e:
            print('OSError: ', e)
        finally:
            return jobconf

def monitor_processes(procs):
    while any(p.is_alive() for p in procs):
        for p in procs:
            print(f'pid :{p.pid} |  is_alive {p.is_alive()} ')
            if not p.is_alive():
                print(f"Process {p.pid} terminated.")
        time.sleep(1)

def run_jobs(jobs_name, total_jobs):
    procs = []
    for name in jobs_name:
        p = Process(target=job_task, args=(total_jobs[name],))
        procs.append(p)
        p.start()
        time.sleep(0.01)

    monitor_thread = threading.Thread(target=monitor_processes, args=(procs,))
    monitor_thread.start()

def init_jobs(data_received: str, clientsocket):
    actual_path = str(Path().resolve())
    fileconf_path = actual_path[0:actual_path.rfind('/')] + '/conf/conf.yml'
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