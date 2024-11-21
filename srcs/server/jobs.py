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
    try:
        with open(fileconf_path, 'r') as file:
            yaml_content = yaml.safe_load(file)
            for jobname, conf in yaml_content.items():
                jobconf = JobConf(name=jobname, conf=conf)
                total_jobs[jobname] = jobconf
    except Exception as e:
        logger.log(f'unexpected error occurred in function [load_conf()]: {e}')
    finally:
        return"Configuration reloaded successfully."

def create_file(file_path):
    fd = os.open(file_path, os.O_CREAT)
    os.close(fd)


def jobs_filtering(jobs_name):
    if start.launched:
        new_jobsname = []
        for key, _ in start.launched.keys():
            if key not in jobs_name or (key in jobs_name):
                return
    return new_jobsname

def parse_jobsname(jobs_name, cmd, clientsocket):
    def check_duplicate(jobs_name):
        return list(set(jobs_name))
    
    jobs_targets = []
    to_remove = []
    new_jobsname = check_duplicate(jobs_name=jobs_name)
    if start.launched:
        launched_jobsname = list(start.launched.keys())
        for jobname in new_jobsname:
            if jobname in launched_jobsname:
                if (not start.launched[jobname].is_alive() and cmd == 'start') or (start.launched[jobname].is_alive() and cmd == 'stop'):
                    jobs_targets.append(jobname)
                else:
                    to_remove.append(jobname)
            elif jobname not in launched_jobsname and cmd == 'start':
                jobs_targets.append(jobname)
        response = ""
        if not jobs_targets:
            print('jobs_targets: ', jobs_targets)
            if to_remove:
                to_remove_response = {
                    'start': f'cannot start job(s) {to_remove} : already started.\n',
                    'stop' : f'cannot stop job(s) {to_remove} : non started.\n'
                }
                response = to_remove_response[cmd]
            if response:
                clientsocket.sendall(bytes(response, 'utf-8'))
        new_jobsname = jobs_targets
    return new_jobsname

def restart_jobs(jobs_name, is_hup:False):
    stop.stop_jobs(jobs_name=jobs_name, is_hup=is_hup)
    start.start_jobs(jobs_name=jobs_name)

def handle_rpl(cmd, clientsocket, jobs_name):
    started = []
    stopped = []

    if start.launched:
        for jobname in jobs_name:
            if start.launched[jobname].is_alive():
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

def is_valid_command(cmd, data_received):
    args = data_received.split()
    args = args[1:len(args)]
    
    command_list = ['start', 'stop', 'reload', 'restart']
    if cmd not in command_list:
        return {'error' : f'*** Unknown syntax: {data_received}'}
    
    command_list.remove('reload')
    not_found = False
    not_found_lst = [] # Job non trouve dans la conf
    if cmd in command_list:
        if not args:
            return {'error': f'command [{cmd}] needs arguments (ex: start ping)'}
        else:
            for arg in args:
                if arg in total_jobs:
                    continue
                else:
                    not_found = True
                    not_found_lst.append(arg)
            if not_found:
                return {'error': f'none of these jobs {not_found_lst} exist in the configuration file'}
    return {'command': cmd}
    
def init_jobs(data_received: str, clientsocket):
    global total_jobs
    jobs_name = []
    try:
        if data_received:
            jobs_name = data_received.split()
            cmd = jobs_name.pop(0)
            response = is_valid_command(cmd=cmd, data_received=data_received)
            print(response)
            if 'error' in response:
                logger.log(response['error'], 'error')
                clientsocket.sendall((bytes(response['error'] + '\n', 'utf-8')))
                server.is_first = False
                return
            else:
                if response['command'] == 'reload':
                    response = load_conf()
                    if not response:
                        level = 'error'
                        response = '[taskmasterd]: Failed to reload conf file'
                    level = 'info'
                    logger.log(response, level)
                    clientsocket.sendall((bytes(response + '\n', 'utf-8')))
                    server.is_first = False
                    return
                else:
                    print('ca rentre la ?')
                    jobs_name = parse_jobsname(jobs_name=jobs_name, cmd=cmd, clientsocket=clientsocket)
                    print('jobsname : ', jobs_name)
                    if jobs_name:
                        exec[cmd](jobs_name=jobs_name)
                        handle_rpl(cmd=cmd, clientsocket=clientsocket, jobs_name=jobs_name)
    except Exception as error:
        logger.log(f'[taskmasterd]: unexpected error occurred in function [ init_jobs ] : {error}', 'error')
    finally:
        server.is_first = False