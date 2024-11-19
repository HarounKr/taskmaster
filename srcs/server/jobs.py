try:
    import yaml, os, start, stop
    from modules.logger_config import logger
    from modules.job_conf import JobConf
    import server
    import start
except ImportError as e:
    raise ImportError(f"[taskmasterd]: Module import failed: {e}")

total_jobs: dict = {}

def load_conf():
    global total_jobs

    fileconf_path = '/tmp/conf.yml'
    print('ça va dans load_conf')
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
    print(jobs_name)
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
        if response:
            clientsocket.sendall(bytes(response, 'utf-8'))
        new_jobsname = jobs_targets
    return new_jobsname

def restart_jobs(jobs_name, is_hup:False):
    stop.stop_jobs(jobs_name=jobs_name, is_hup=is_hup)
    start.start_jobs(jobs_name=jobs_name)

def handle_rpl(cmd, launched, clientsocket, jobs_name):
    started = []
    stopped = []

    if launched:
        for jobname in jobs_name:
            if launched[jobname].is_alive():
                started.append(jobname)
            else:
                stopped.append(jobname) 
        to_return_response = {
            'start': f'The following task(s) have been successfully started: {", ".join(started)}.\n',
            'stop': f'The following task(s) have been successfully stopped: {", ".join(stopped)}.\n',
        }
        response = to_return_response[cmd]
        if response:
            clientsocket.sendall(bytes(response, 'utf-8'))

exec = {
    'start': lambda jobs_name: start.start_jobs(jobs_name=jobs_name),
    'stop': lambda jobs_name: stop.stop_jobs(jobs_name=jobs_name, is_hup=False),
    'restart': lambda jobs_name: restart_jobs(jobs_name=jobs_name, is_hup=False),
}

def init_jobs(data_received: str, clientsocket):
    global total_jobs
    is_first = server.is_first
    launched = start.launched
    jobs_name = [] 
    try:
        if data_received:
            jobs_name = data_received.split()
            cmd = jobs_name.pop(0)
            print('is_first : ', is_first)
            if cmd == 'reload':
                load_conf()
            if cmd != 'reload':
                jobs_name = parse_jobsname(jobs_name=jobs_name, cmd=cmd, clientsocket=clientsocket)
                if jobs_name:
                    exec[cmd](jobs_name=jobs_name)
                handle_rpl(cmd=cmd, launched=launched, clientsocket=clientsocket, jobs_name=jobs_name)
    except Exception as error:
        logger.log(f'[taskmasterd]: unexpected error occurred in function [ init_jobs ] : {error}', 'error')
    finally:
        is_first = False