try:
    import yaml, subprocess, os, threading, time, signal, sys
    from modules.logger_config import logger
    from modules.job_conf import JobConf
    from start import start_jobs
    import start
except ImportError as e:
    raise ImportError(f"[taskmasterd]: Module import failed: {e}")

is_first = True
total_jobs: dict = {}


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


def jobs_filtering(jobs_name):
    launched = start.launched
    if start.launched:
        new_jobsname = []
        for key, _ in launched.keys():
            if key not in jobs_name or (key in jobs_name):
                return
    return new_jobsname

def parse_jobsname(jobs_name, cmd, clientsocket):
    launched = start.launched

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

exec = {
    'start': start_jobs,
    'stop': stop_jobs,
    'reload': restart_jobs,
    'restart' : restart_jobs,
}


def init_jobs(data_received: str, clientsocket):
    global total_jobs
    global is_first
   
    jobs_name = [] 
    try:
        if data_received:
            jobs_name = data_received.split()
            cmd = jobs_name.pop(0)
            if is_first is True or cmd == 'reload':
                if cmd == 'reload':
                    reloaded = True
                load_conf()
            elif cmd == 'restart':
                reloaded = False
            jobs_name = parse_jobsname(jobs_name=jobs_name, cmd=cmd, clientsocket=clientsocket)
            if jobs_name:
                exec[cmd](jobs_name=jobs_name)
    except Exception as error:
        logger.log(f'[taskmasterd]: unexpected error occurred in function [ init_jobs ] : {error}', 'error')
    finally:
        is_first = False