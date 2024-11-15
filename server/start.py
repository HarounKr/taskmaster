try:
    import subprocess, os, threading, time, signal, sys
    from modules.logger_config import logger
    from multiprocessing import Process, Queue
    import jobs
except ImportError as e:
    raise ImportError(f"[taskmasterd]: Module import failed: {e}")

to_reload = []
queue_out = Queue()
queue_sighub = Queue()
queue_value = {}
reloaded = False
procs: list = []
launched: dict = {}

def start_procs(numprocs: int, initchild, cmd, env:None) -> list:
    procs = []
    for _ in range(0, numprocs):
        start_time = time.time()
        process = subprocess.Popen(cmd.split(), text=True, preexec_fn=initchild, env=env)
        procs.append((process, 0, start_time))
    return procs

def sig_handler(procs, jobname, queue_sighub):
    def kill_childs(signum, frame):
        logger.log(f"[taskmasterd]: received signal {signum}. Terminating child processes...", 'info')
        for proc, _, _ in procs:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                finally:
                    logger.log(f'[taskmasterd]: process #{proc.pid} terminated', 'info')
        sys.exit(0)
    
    def handle_sighup(signum, frame):
        pid = os.getpid()
        print(f'{jobname} : {pid}')
        logger.log(f"[taskmasterd]: job {jobname} with pid #{pid} received SIGHUP - reloading configuration..", 'info')
        queue_sighub.put(jobname)
        #load_conf()
        #stop_jobs([jobname])
        #start_jobs([jobname])

    signal.signal(signal.SIGHUP, handle_sighup)
    signals = [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT, signal.SIGABRT, signal.SIGFPE, signal.SIGSEGV]
    for sig in signals:
        signal.signal(sig, kill_childs)

def job_task(jobconf, queue_out, queue_sighub):
    procs = []

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
            procs = start_procs(numprocs=jobconf.numprocs, initchild=initchild, cmd=jobconf.cmd, env=child_env)
            if procs:
                sig_handler(procs=procs, jobname=jobconf.name, queue_sighub=queue_sighub)
                ppid = os.getpid()
                size = len(procs)
                cpids = []
                for proc, _, _ in procs:
                    cpids.append(proc.pid)
                logger.log(f"[taskmasterd]: job {jobconf.name} started with pid #{ppid} and {size} child(s) #{cpids}", 'info')
                pids = {} 
                pids[ppid] = cpids
                queue_out.put(pids)
                while True:
                    new_procs = []
                    current_time = time.time()
                    for proc, retries , start_time in procs:
                        # logger.log(f"current_time : {current_time} start_time : {start_time}\n result : {current_time - start_time}")
                        if proc.poll() is not None:
                            logger.log(f"[taskmasterd]: process #{proc.pid} terminated with exit code {proc.returncode}", 'info')
                            if proc.returncode not in jobconf.exitcodes and jobconf.autorestart == "unexpected":
                                should_restart = (current_time - start_time) < jobconf.starttime or retries < jobconf.startretries
                                if should_restart:
                                    logger.log(f"[taskmasterd]: restarting process #{proc.pid}. Attempt {retries + 1} | start time : {current_time - start_time}s", 'info')
                                    new_process = subprocess.Popen(jobconf.cmd.split(), text=True, preexec_fn=initchild, env=child_env)
                                    new_procs.append((new_process, retries + 1, time.time()))
                                    cpids.append(new_process.pid)
                                else:
                                    logger.log(f"[taskmasterd]: process #{proc.pid} has exceeded the maximum retry | start time : {current_time - start_time}s", 'info')
                            elif jobconf.autorestart is True and retries < jobconf.startretries:
                                new_process = subprocess.Popen(jobconf.cmd.split(), text=True, preexec_fn=initchild, env=child_env)
                                new_procs.append((new_process, retries + 1, time.time()))
                                cpids.append(new_process.pid)
                            pids[ppid] = cpids
                            queue_out.put(pids)
                        else:
                            new_procs.append((proc, retries, start_time))
                        time.sleep(1)
                    procs = new_procs
                    if not procs:
                        break
        except OSError as e:
            logger.log(f'[taskmasterd]: unexpected error occurred in function [ job_task ] : {e} ', 'error')

def monitor_processes(procs, queue_out, queue_sighub):
    while True:
        while not queue_out.empty():
            queue_value.update(queue_out.get())
        while not queue_sighub.empty():
            jobname = queue_sighub.get()

            if isinstance(jobname, str):
                to_reload.append(jobname)
        if to_reload:
            print('to reload : ', to_reload)
        for p in procs:
            if not p.is_alive():
                logger.log(f"[taskmasterd]: process #{p.pid} terminated.", 'info')
                if p.pid in list(queue_value.keys()):
                    for cpid in queue_value[p.pid]:
                        try:
                            proc_exist = os.kill(cpid, 0)
                            if proc_exist is None:
                                os.kill(cpid ,signal.SIGTERM)
                                time.sleep(0.1)
                                logger.log(f"[taskmasterd]: child process #{cpid} terminated by SIGTERM signal.", 'info')
                        except:
                            logger.log(f"[taskmasterd]: child process #{cpid} does not exit.", 'info')
                procs.remove(p)
                queue_value.pop(p.pid, None)
        if not procs:
            break
        time.sleep(1)

def start_jobs(jobs_name):
    global procs
    global launched
   
    logger.log(f"[taskmasterd]: start job(s) {jobs_name}", 'info')
    for name in jobs_name:
        p = Process(target=job_task, args=(jobs.total_jobs[name], queue_out, queue_sighub))
        procs.append(p)
        p.start()
        launched[name] = p
        time.sleep(0.01)
    
    if not reloaded:
        monitor_thread = threading.Thread(target=monitor_processes, args=(procs, queue_out, queue_sighub))
        monitor_thread.start()
    if to_reload:
        print('to reload : ', to_reload)