import yaml, subprocess
from pathlib import Path
from modules.job_conf import JobConf
from multiprocessing import Process, Queue

def create_file(file_path):
    file_name = file_path[file_path.rfind('/'):len(file_path)]
    f = open(file_name, os.O_CREAT)
    f.close()

def job_task(jobconf, queue_out):
    stdout_path = ""
    stderr_path = ""
    if hasattr(jobconf, 'cmd') and jobconf.cmd:
        try:
            if hasattr(jobconf, 'workingdir') and jobconf.workingdir:
                os.chdir(jobconf.workingdir)
                print(os.getcwd())
            if hasattr(jobconf, 'umask') and jobconf.umask:
                octal_int =  int(str(jobconf.umask), 8)
                octal_mask = oct(octal_string)
                os.umask(octal_mask)
            if hasattr(jobconf, 'stdout') and jobconf.stdout:
                create_file(jobconf.stdout)
        except OSError as e:
            print(e)
        process = subprocess.Popen(jobconf.cmd.split(), stdout=subprocess.PIPE, sterr=subprocess.PIPE)
        out, err = process.communicate()
        print('Subprocess PID:', process.pid)
        print('returncode: ', process.returncode)
        print(out.decode())

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
            job_process = Process(target=job_task, args=(total_jobs[name], queue_out))
            # queue_in.put(total_jobs[name])
            job_process.start()
            # job_process.append(p)
        else:
            not_found.append(name)
    # for process in job_process:
    #     process.join()
    while queue_out.empty() is not False:
        updated_jobconf = queue_out.get()
        print('name: ', updated_jobconf.name);
        total_jobs[updated_jobconf.name] = updated_jobconf
    print('alors ??\n', total_jobs)
    monitoring_process = Process(target=monitoring_task, args=[total_jobs])
    monitoring_process.join()
    
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