try:
    import subprocess, os, signal, sys
    from modules.logger_config import logger
except ImportError as e:
    raise ImportError(f"[taskmasterd]: Module import failed: {e}")



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