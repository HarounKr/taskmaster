import yaml
from pathlib import Path
from modules.job_conf import JobConf
from multiprocessing import Process, Queue

def job_task(jobconf, queue_out):
    # jobconf = queue_in.get()
    jobconf.is_started = True
    queue_out.put(jobconf)

def run_jobs(jobs_name, total_jobs):
    not_found: list = []
    processes: list = []
    # queue_in = Queue()
    queue_out = Queue()
    for name in jobs_name:
        print(name)
        if name in list(total_jobs.keys()):
            p = Process(target=job_task, args=(total_jobs[name], queue_out))
            # queue_in.put(total_jobs[name])
            p.start()
            processes.append(p)
        else:
            not_found.append(name)
    for process in processes:
        process.join()
    while not queue_out.empty():
        updated_jobconf = queue_out.get()
        print('name: ', updated_jobconf.name);
        total_jobs[updated_jobconf.name] = updated_jobconf
    print('alors ??\n', total_jobs)
    
    if not_found:
        response = ', '.join(not_found) + ': job(s) not found.\n'
        clientsocket.sendall(bytes(response, 'utf-8'))

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