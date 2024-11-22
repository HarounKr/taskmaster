try:
    import subprocess, os, threading, time, signal, jobs
    from modules.logger_config import logger
    from multiprocessing import Process, Queue
    from signals import sig_handler
    from stop import stop_jobs
except ImportError as e:
    raise ImportError(f"[taskmasterd]: Module import failed: {e}")

to_reload = []
queue_out = Queue()
queue_sighub = Queue()
queue_jobpids = {}
reloaded = False
job_procs: list = []
launched: dict = {}
monitoring_thread = None

PR_SET_NAME = 15

def start_procs(numprocs: int, initchild, cmd, env:None) -> list:
    procs = []
    for _ in range(0, numprocs):
        start_time = time.time()
        process = subprocess.Popen(cmd.split(), text=True, preexec_fn=initchild, env=env)
        procs.append((process, 0, start_time))
    return procs

def job_task(jobconf, queue_out, queue_sighub):
    child_procs = []

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
            if hasattr(jobconf, 'stdout') and jobconf.stdout:
                stdout_fd = os.open(jobconf.stdout, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
                os.dup2(stdout_fd, 1) # Redirige la sortie du processus enfant vers le fichier
                os.close(stdout_fd)
            if hasattr(jobconf, 'stderr') and jobconf.stderr:
                stderr_fd = os.open(jobconf.stderr, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
                os.dup2(stderr_fd, 2)
                os.close(stderr_fd)        
        try:
            time.sleep(jobconf.starttime)
            child_procs = start_procs(numprocs=jobconf.numprocs, initchild=initchild, cmd=jobconf.cmd, env=child_env)
            if child_procs:
                sig_handler(procs=child_procs, jobname=jobconf.name, queue_sighub=queue_sighub)
                job_pid = os.getpid()
                size = len(child_procs)
                child_pids = []
                for proc, _, _ in child_procs:
                    child_pids.append(proc.pid)
                logger.log(f"[taskmasterd]: job -- {jobconf.name} -- started with pid #{job_pid} and {size} child(s) #{child_pids}", 'info')
                total_pids = {}
                total_pids[job_pid] = child_pids
                queue_out.put(total_pids)
                while True:
                    new_procs = []
                    current_time = time.time()
                    for proc, retries , start_time in child_procs:
                        # logger.log(f"current_time : {current_time} start_time : {start_time}\n result : {current_time - start_time}")
                        if proc.poll() is not None:
                            logger.log(f"[taskmasterd]: process #{proc.pid} terminated with exit code {proc.returncode}", 'info')
                            if proc.returncode not in jobconf.exitcodes and jobconf.autorestart == "unexpected":
                                should_restart = (current_time - start_time) < jobconf.starttime or retries < jobconf.startretries
                                if should_restart:
                                    logger.log(f"[taskmasterd]: restarting process #{proc.pid}. Attempt {retries + 1}", 'info')
                                    new_process = subprocess.Popen(jobconf.cmd.split(), text=True, preexec_fn=initchild, env=child_env)
                                    new_procs.append((new_process, retries + 1, time.time()))
                                    child_pids.append(new_process.pid)
                                    child_pids.pop(child_pids.index(proc.pid))
                                else:
                                    logger.log(f"[taskmasterd]: process #{proc.pid} has exceeded the maximum retry {jobconf.startretries}", 'info')
                            elif jobconf.autorestart is True:
                                logger.log(f"[taskmasterd]: restarting process #{proc.pid}", 'info')
                                new_process = subprocess.Popen(jobconf.cmd.split(), text=True, preexec_fn=initchild, env=child_env)
                                new_procs.append((new_process, retries + 1, time.time()))
                                child_pids.append(new_process.pid)
                                child_pids.pop(child_pids.index(proc.pid))
                            total_pids[job_pid] = child_pids
                            queue_out.put(total_pids)
                        else:
                            new_procs.append((proc, retries, start_time))
                        time.sleep(0.5)
                    child_procs = new_procs
                    if not child_procs:
                        break
        except OSError as e:
            logger.log(f'[taskmasterd]: unexpected error occurred in function [ job_task ] : {e} ', 'error')

def monitor_processes(procs, queue_out, queue_sighub):
    global to_reload

    while True:
        while not queue_out.empty():
            queue_jobpids.update(queue_out.get())
        while not queue_sighub.empty():
            jobname = queue_sighub.get()
            if isinstance(jobname, str):
                to_reload.append(jobname)

        if to_reload:
            stop_jobs(jobs_name=to_reload, is_hup=True)
            jobs.load_conf()
            start_jobs(jobs_name=to_reload)
            to_reload = []

        for process in procs[:]:
            if not process.is_alive():
                logger.log(f"[taskmasterd]: process #{process.pid} terminated.", 'info')
                if process.pid in queue_jobpids:
                    for cpid in queue_jobpids[process.pid]:
                        try:
                            proc_exist = os.kill(cpid, 0)
                            if proc_exist is None:
                                os.kill(cpid ,signal.SIGTERM)
                                time.sleep(0.1)
                                logger.log(f"[taskmasterd]: child process #{cpid} terminated by SIGTERM signal.", 'info')
                        except:
                            logger.log(f"[taskmasterd]: child process #{cpid} does not exist.", 'info')
                try:
                    procs.remove(process)
                    queue_jobpids.pop(process.pid, None)
                except ValueError as e:
                    logger.log(f"[taskmasterd]: Error removing process #{process.pid}: {e}", 'error')
        time.sleep(1)

def start_jobs(jobs_name):
    global job_procs
    global launched
    global monitoring_thread
    logger.log(f"[taskmasterd]: start job(s) {jobs_name}", 'info')

    for name in jobs_name:
        p = Process(target=job_task, args=(jobs.total_jobs[name], queue_out, queue_sighub))
        job_procs.append(p)
        p.start()
        launched[name] = p
        time.sleep(0.01)

    if monitoring_thread is None:
        monitoring_thread = threading.Thread(target=monitor_processes, args=(job_procs, queue_out, queue_sighub))
        monitoring_thread.start()