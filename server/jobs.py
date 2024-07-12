import yaml, subprocess, os
from pathlib import Path
from modules.job_conf import JobConf
from multiprocessing import Process, Queue
from concurrent.futures import ProcessPoolExecutor, as_completed

def create_file(file_path):
    # file_name = file_path[file_path.rfind('/'):len(file_path)]
    # print(file_name)
    fd = os.open(file_path, os.O_CREAT)
    os.close(fd)

def job_task(jobconf):
    stdout_path = ""
    stderr_path = ""
    if hasattr(jobconf, 'cmd') and jobconf.cmd:
        try:
            # if hasattr(jobconf, 'workingdir') and jobconf.workingdir:
            #     os.chdir(jobconf.workingdir)
            #     print(os.getcwd())
            # if hasattr(jobconf, 'umask') and jobconf.umask:
            #     print('umask: ', jobconf.umask)
            #     os.umask(jobconf.umask)
            # if hasattr(jobconf, 'stdout') and jobconf.stdout:
            #     create_file(file_path=jobconf.stdout)
            # if hasattr(jobconf, 'stderr') and jobconf.stderr:
            #     create_file(file_path=jobconf.stderr)
            # print(jobconf.cmd.split())
            # process = subprocess.Popen(jobconf.cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # out, err = process.communicate()
            # print('Subprocess PID:', process.pid)
            # print('returncode: ', process.returncode)
            # print('command output: ', out.decode())
            jobconf.is_started = True
        except OSError as e:
            print('OSError: ', e)
        finally:
            return jobconf

def run_jobs(jobs_name, total_jobs):
    not_found = []
    jobs = {}
    # Créer un pool de processus
    with ProcessPoolExecutor() as executor:
        # Soumettre les tâches
        for name in jobs_name:
            if name in list(total_jobs.keys()):
                # Soumission de la tâche job_task avec les arguments nécessaires
                job = executor.submit(job_task, total_jobs[name])
                print(type(job.result()))
                print(name)
                jobs[job] = name
            else:
                not_found.append(name)

        # Récupération des résultats à mesure qu'ils sont disponibles
        for job in as_completed(jobs):
            job_name = job.result().name
            try:
                print(job.result().name)
                updated_jobconf = job.result()  # Récupérer le résultat de la tâche
                # print('name: ', updated_jobconf[job_name])
                total_jobs[job_name] = updated_jobconf  # Mettre à jour le dictionnaire des tâches
            except Exception as e:
                print(f"Job {job_name} generated an exception: {e}")
    print('Total Jobs a la sortie\n', total_jobs['ping'])
    print('ca sort ??')
    # monitoring_process = Process(target=monitoring_task, args=[total_jobs])
    # monitoring_process.join()
    
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