try:
    import yaml, subprocess, os, threading, time, signal, sys
    from pathlib import Path
    from modules.job_conf import JobConf
    from multiprocessing import Process, Queue
    from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor 
except ImportError as e:
    raise ImportError(f"Module import failed: {e}")

procs: list = []
launched: dict = {}
total_jobs: dict = {}
is_first = True
queue_value = [] 
def create_file(file_path):
    fd = os.open(file_path, os.O_CREAT)
    os.close(fd)

def start_procs(numprocs: int, initchild, cmd, env:None) -> list:
    procs = []
    for i in range(0, numprocs):
        start_time = time.time()
        process = subprocess.Popen(cmd.split(), text=True, preexec_fn=initchild, env=env)
        procs.append((process, 0, start_time))
    return procs

def job_task(jobconf, queue_out):
    print(f"Monitoring process : {os.getpid()}")
    print('Name : ', jobconf.name)
    procs = []
    def kill_childs(signum, frame):
        print(f"Received signal {signum}. Terminating child processes...")
        for proc, _, _ in procs:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                finally:
                    print(f'process {proc.pid} terminated')
        sys.exit(0)

    signals = [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT]
    for sig in signals:
        signal.signal(sig, kill_childs)

    if hasattr(jobconf, 'cmd') and jobconf.cmd:
        child_env = None
        if hasattr(jobconf, 'env') and jobconf.env:
            child_env = os.environ.copy()
            for key, value in jobconf.env.items():
                child_env[key] = value
        def initchild():
            if hasattr(jobconf, 'umask') and jobconf.umask:
                os.umask(jobconf.umask)
            if hasattr(jobconf, 'workingdir') and jobconf.workingdir:
                os.chdir(jobconf.workingdir)
            # if hasattr(jobconf, 'stdout') and jobconf.stdout:
            #     stdout_fd = os.open(jobconf.stdout, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
            #     os.dup2(stdout_fd, 1) # Redirige la sortie du processus enfant vers le fichier
            #     os.close(stdout_fd)
            # if hasattr(jobconf, 'stderr') and jobconf.stderr:
            #     stderr_fd = os.open(jobconf.stderr, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
            #     os.dup2(stderr_fd, 2)
            #     os.close(stderr_fd)        
        try:
            procs = start_procs(numprocs=jobconf.numprocs, initchild=initchild, cmd=jobconf.cmd, env=child_env)
            cpids = [] 
            for proc, retries , start_time in procs:
                cpids.append(proc.pid)
            ppid = os.getpid()
            pids = {}  
            pids[ppid] = cpids 
            queue_out.put(pids)
            while True:
                new_procs = []
                current_time = time.time()
                for proc, retries , start_time in procs:
                    # print(f"current_time : {current_time} start_time : {start_time}\n result : {current_time - start_time}")
                    if proc.poll() is not None:
                        print(f"Process {proc.pid} terminated with exit code {proc.returncode}")
                        if proc.returncode not in jobconf.exitcodes and jobconf.autorestart == "unexpected":
                            should_restart = (current_time - start_time) < jobconf.starttime or retries < jobconf.startretries
                            if should_restart:
                                print(f"Restarting process {proc.pid}. Attempt {retries + 1} | start time : {current_time - start_time}s")
                                new_process = subprocess.Popen(jobconf.cmd.split(), text=True, preexec_fn=initchild, env=child_env)
                                new_procs.append((new_process, retries + 1, time.time()))
                            else:
                                print(f"Process {proc.pid} has exceeded the maximum retry | start time : {current_time - start_time}s")
                        elif jobconf.autorestart is True and retries < jobconf.startretries:
                            new_process = subprocess.Popen(jobconf.cmd.split(), text=True, preexec_fn=initchild, env=child_env)
                            new_procs.append((new_process, retries + 1, time.time()))
                    else:
                        new_procs.append((proc, retries, start_time))
                    time.sleep(1)
                procs = new_procs
                if not procs:
                    break
        except OSError as e:
            print('OSError: ', e)
        finally:
            return jobconf

def monitor_processes(procs, queue_out):
    results = []
    while not queue_out.empty():
        results.append(queue_out.get())
    print(f'Queue Results:{results} ')
    while True:
        for p in procs:
            print(f'pid :{p.pid} |  is_alive {p.is_alive()} ')
            if not p.is_alive():
                print(f"Process {p.pid} terminated.")
                procs.remove(p)
        if not procs:
            break
        time.sleep(1)

def start_jobs(jobs_name):
    global procs
    global launched
    global total_jobs

    queue_out = Queue()
    for name in jobs_name:
        p = Process(target=job_task, args=(total_jobs[name], queue_out))
        procs.append(p)
        p.start()
        launched[name] = p
        time.sleep(0.01)

    monitor_thread = threading.Thread(target=monitor_processes, args=(procs, queue_out))
    monitor_thread.start()

def jobs_filtering(jobs_name):

    if launched:
        new_jobsname = []
        for key, value in launched.keys():
            if key not in jobs_name or (key in jobs_name):
                return
    return new_jobsname

def add_conf(data_received: str):
    global total_jobs

    fileconf_path = '/tmp/conf.yml'

    with open(fileconf_path, 'r') as file:
        yaml_content = yaml.safe_load(file)
        for jobname, conf in yaml_content.items():
            jobconf = JobConf(name=jobname, conf=conf)
            total_jobs[jobname] = jobconf
            if data_received is None and hasattr(jobconf, 'autostart') and jobconf.autostart is True:
                jobs_name.append(jobconf.name)

def stop_task(jobs_name):

    if launched:
        stop_signals = {
            'TERM': signal.SIGTERM,
            'INT':  signal.SIGINT,
            'QUIT': signal.SIGQUIT,
            'KILL': signal.SIGKILL,
        }
        for jobname in jobs_name:
            if jobname in list(launched.keys()):
                job_process = launched[jobname]
                if job_process.is_alive():
                    print(f'job : {jobname} is already alive : Terminating ...')
                    stop_sig = total_jobs[jobname].stopsignal
                    stop_time = total_jobs[jobname].stoptime
                    pid = job_process.pid
                    os.kill(pid, stop_signals[stop_sig][0])
                    time.sleep(stop_time)
                    if job_process.is_alive():
                        os.kill(pid, signal.SIGKILL)
                        time.sleep(0.2)
                        print(f'Job {jobname} could not be stopped by {stop_sig} signal and had terminated by SIGKILL')
                    else:
                        print(f'Job "{jobname}" with PID {pid} was terminated by the {stop_sig} signal.')
                else:
                    print(f'Job {jobname} is NOT alive')
            else:
                print(f'Job "{jobname}" is not found')
    return

def stop_jobs(jobs_name: str):
    global launched
    global total_jobs

    stop_thread = threading.Thread(target=stop_task, args=(jobs_name,))
    stop_thread.start()
    stop_thread.join()

    return

def init_jobs(data_received: str):
    global launched
    global total_jobs
    global is_first

    actual_path = str(Path().resolve())
    jobs_name = []
    print('is_first \n: ', is_first)
    try:
        print('data_received: ', data_received)
        if data_received:
            jobs_name = data_received.split()
            cmd = jobs_name.pop(0)

            if is_first is True or cmd == 'reload':
                add_conf(data_received=data_received)
            if cmd == 'start':
                print('ca rentre dans le start')
                start_jobs(jobs_name=jobs_name)
            elif cmd == 'stop':
                print('ca rentre dans le stop')
                stop_jobs(jobs_name=jobs_name)
            elif cmd in ['restart', 'reload']:
                stop_jobs(jobs_name=jobs_name)
                start_jobs(jobs_name)
        # jobs_filtering(jobs_name)
   
    except Exception as error:
        print(f'init_jobs: {error}')
    finally:
        is_first = False