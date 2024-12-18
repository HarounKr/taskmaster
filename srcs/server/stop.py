import start, jobs, os, time, signal, threading
from modules.logger_config import logger


def stop_task(jobs_name, is_hup: False):
    launched = start.launched
    total_jobs = jobs.total_jobs

    if launched:
        try:
            stop_signals = {
                'TERM': signal.SIGTERM,
                'INT':  signal.SIGINT,
                'QUIT': signal.SIGQUIT,
                'KILL': signal.SIGKILL,
                'HUP': signal.SIGHUP
            }
            for jobname in jobs_name:
                if jobname in launched:
                    job_process = launched[jobname]
                    if job_process.is_alive():
                        if is_hup:
                            stop_sig = 'TERM'
                        else: 
                            stop_sig = total_jobs[jobname].stopsignal.upper()
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
        except Exception as e:
            logger.log(f"[taskmasterd]: Error at stop_task in stop.py : {e}", 'error')


def stop_jobs(jobs_name, is_hup:False):
    logger.log(f"[taskmasterd]: stop job(s) {jobs_name}", 'info')
    stop_thread = threading.Thread(target=stop_task, args=(jobs_name, is_hup))
    stop_thread.start()
    stop_thread.join()