try:
    import yaml, subprocess, os, threading, time, signal, sys
    from modules.logger_config import logger
    from modules.job_conf import JobConf
    from multiprocessing import Process, Queue, Pipe
except ImportError as e:
    raise ImportError(f"[taskmasterd]: Module import failed: {e}")

procs: list = []
launched: dict = {}
total_jobs: dict = {}
is_first = True
queue_value = {}

def load_conf():
    global total_jobs

    fileconf_path = '/tmp/conf.yml'
    with open(fileconf_path, 'r') as file:
        yaml_content = yaml.safe_load(file)
        for jobname, conf in yaml_content.items():
            jobconf = JobConf(name=jobname, conf=conf)
            total_jobs[jobname] = jobconf

def create_file(file_path):
    fd = os.open(file_path, os.O_CREAT)
    os.close(fd)

def start_procs(numprocs: int, initchild, cmd, env:None) -> list:
    procs = []
    for _ in range(0, numprocs):
        start_time = time.time()
        process = subprocess.Popen(cmd.split(), text=True, preexec_fn=initchild, env=env)
        procs.append((process, 0, start_time))
    return procs

def sig_handler(procs, jobname, conn):
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
        logger.log("[taskmasterd]: job {jobname} with pid #{pid} received SIGHUP - reloading configuration..", 'info')
        conn.send('SIGHUP recu')
        #conn.close()
        #load_conf()
        #stop_jobs([jobname])
        #start_jobs([jobname])

    signal.signal(signal.SIGHUP, handle_sighup)
    signals = [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT, signal.SIGABRT, signal.SIGFPE, signal.SIGSEGV]
    for sig in signals:
        signal.signal(sig, kill_childs)

def job_task(jobconf, queue_out, conn):
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
                sig_handler(procs=procs, jobname=jobconf.name, conn=conn)
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

def monitor_processes(procs, queue_out, parent_conn):
    while True:
        while not queue_out.empty():
            queue_value.update(queue_out.get())
        #print('block')
        message = parent_conn.recv()
        if message:
            print('messag from child :' , {message})
        #print('non block')
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
    global total_jobs

    logger.log(f"[taskmasterd]: start job(s) {jobs_name}", 'info')
    queue_out = Queue()
    parent_conn, child_conn = Pipe()
    for name in jobs_name:
        p = Process(target=job_task, args=(total_jobs[name], queue_out, child_conn))
        procs.append(p)
        p.start()
        launched[name] = p
        time.sleep(0.01)
    message = parent_conn.recv()
    if message:
        print('messag from child :' , {message})
    monitor_thread = threading.Thread(target=monitor_processes, args=(procs, queue_out, parent_conn))
    monitor_thread.start()

def jobs_filtering(jobs_name):
    if launched:
        new_jobsname = []
        for key, _ in launched.keys():
            if key not in jobs_name or (key in jobs_name):
                return
    return new_jobsname

def stop_task(jobs_name):
    global launched
    if launched:
        stop_signals = {
            'TERM': signal.SIGTERM,
            'INT':  signal.SIGINT,
            'QUIT': signal.SIGQUIT,
            'KILL': signal.SIGKILL,
            'HUP': signal.SIGHUP
        }
        print(jobs_name)
        for jobname in jobs_name:
            if jobname in list(launched.keys()):
                job_process = launched[jobname]
                if job_process.is_alive():
                    stop_sig = total_jobs[jobname].stopsignal
                    stop_time = total_jobs[jobname].stoptime
                    pid = job_process.pid
                    logger.log(f'[taskmasterd]: job : {jobname} is already alive : Terminating ...', 'info')
                    os.kill(pid, stop_signals[stop_sig])
                    time.sleep(stop_time)
                    if job_process.is_alive():
                        os.kill(pid, signal.SIGKILL)
                        time.sleep(0.2)
                        logger.log(f'[taskmasterd]: job {jobname} with PID #{pid} could not be stopped by SIG{stop_sig} signal and had terminated by SIGKILL', 'info')
                    else:
                        logger.log(f'[taskmasterd]: job "{jobname}" with PID #{pid} was terminated by SIG{stop_sig} signal.', 'info')
                else:
                    logger.log(f'[taskmasterd]: job {jobname} is NOT alive', 'info')
            else:
                logger.log(f'[taskmasterd]: job "{jobname}" is not found', 'info')

def stop_jobs(jobs_name: str):
    logger.log(f"[taskmasterd]: stop job(s) {jobs_name}", 'info')
    stop_thread = threading.Thread(target=stop_task, args=(jobs_name,))
    stop_thread.start()
    stop_thread.join()

def parse_jobsname(jobs_name, cmd, clientsocket):
    global launched

    def check_duplicate(jobs_name):
        new_jobsname = []
        for item in jobs_name:
            if item not in new_jobsname:
                new_jobsname.append(item)
        return new_jobsname
    
    jobs_targets = []
    to_remove = [] 
    new_jobsname = check_duplicate(jobs_name=jobs_name)
    launched_jobsname = list(launched.keys())
    if launched:
        for jobname in new_jobsname:
            if jobname in launched_jobsname:
                if (not launched[jobname].is_alive() and cmd == 'start') or (launched[jobname].is_alive() and cmd == 'stop'):
                    jobs_targets.append(jobname)
                else:
                    to_remove.append(jobname)
            elif jobname not in launched_jobsname and cmd == 'start':
                jobs_targets.append(jobname)
        response = ""
        if to_remove:
            to_remove_response = {
                'start': f'cannot start job(s) {to_remove} : already started.\n',
                'stop' : f'cannot stop job(s) {to_remove} : non started.\n'
            }
            response += to_remove_response[cmd]
        if jobs_targets:
            to_return_response ={
                'start': f'The following task(s) have been successfully started: {", ".join(jobs_targets)}.\n',
                'stop': f'The following task(s) have been successfully stopped: {", ".join(jobs_targets)}.\n',
            }
            response += to_return_response[cmd]
        if response:
            clientsocket.sendall(bytes(response, 'utf-8'))
        new_jobsname = jobs_targets
    return new_jobsname

def restart_jobs(jobs_name):
    stop_jobs(jobs_name=jobs_name)
    start_jobs(jobs_name=jobs_name)

exec ={
    'start': start_jobs,
    'stop': stop_jobs,
    'reload': restart_jobs,
    'restart' : restart_jobs,
}

def test(sig, frame):
    if sig == signal.SIGHUP:
        print('SIGHUP Receiv')

def init_jobs(data_received: str, clientsocket):
    global launched
    global total_jobs
    global is_first
   
    jobs_name = []
    # signal.signal(signalnum=signal.SIGHUP, handler=test)
    try:
        if data_received:
            jobs_name = data_received.split()
            cmd = jobs_name.pop(0)
            if is_first is True or cmd == 'reload':
                load_conf()
            jobs_name = parse_jobsname(jobs_name=jobs_name, cmd=cmd, clientsocket=clientsocket)
            if jobs_name:
                exec[cmd](jobs_name=jobs_name)
    except Exception as error:
        logger.log(f'[taskmasterd]: unexpected error occurred in function [ init_jobs ] : {error}', 'error')
    finally:
        is_first = False