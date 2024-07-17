import subprocess
import concurrent.futures
# def run_job(jobconf):
#     """Exécute un seul job selon la configuration spécifiée."""
#     try:
#         if 'workingdir' in jobconf:
#             cwd = jobconf['workingdir']
#         else:
#             cwd = None

#         stdout_file = open(jobconf['stdout'], 'a') if 'stdout' in jobconf else subprocess.PIPE
#         stderr_file = open(jobconf['stderr'], 'a') if 'stderr' in jobconf else subprocess.PIPE

#         process = subprocess.Popen(jobconf['cmd'].split(), cwd=cwd, stdout=stdout_file, stderr=stderr_file)
#         jobconf['process'] = process
#         jobconf['status'] = 'running'
#         return process
#     except Exception as e:
#         print(f"Error starting job: {e}")
#         jobconf['status'] = 'failed'

# def monitor_jobs(total_jobs):
#     """Surveille et redémarre les jobs si nécessaire selon la configuration."""
#     while True:
#         for job_name, jobconf in total_jobs.items():
#             process = jobconf.get('process')
#             if process and process.poll() is not None:  # Le processus s'est terminé
#                 if process.returncode != 0 and jobconf.get('autorestart', False):
#                     print(f"Job {job_name} failed with return code {process.returncode}. Restarting...")
#                     run_job(jobconf)  # Redémarrer le job
#                 else:
#                     print(f"Job {job_name} completed with return code {process.returncode}.")
#                     jobconf['status'] = 'completed'
#             elif not process:
#                 # Si aucun processus n'est associé, démarrer le job
#                 print(f"Starting job {job_name}...")
#                 run_job(jobconf)

#         time.sleep(10)  # Pause de 10 secondes entre les vérifications

def run_command(command):
    """ Exécute une commande système et retourne la sortie. """
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        return (command, result.stdout)
    except Exception as e:
        return (command, str(e))

def main():
    commands = ["ping -c google.com", "echo Hello", "ls -l"]
    results = []
    
    # Créer un ThreadPoolExecutor pour gérer les threads
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Soumettre les commandes à l'executor
        futures = {executor.submit(run_command, cmd): cmd for cmd in commands}
        
        for future in concurrent.futures.as_completed(futures):
            cmd = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                print(f'{cmd} generated an exception: {exc}')
            else:
                results.append(result)
                print(f'Command: {result[0]}, Output: {result[1]}')
                
    commands = ["echo Fais pas le fou par contre"]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Soumettre les commandes à l'executor
        futures = {executor.submit(run_command, cmd): cmd for cmd in commands}
        
        for future in concurrent.futures.as_completed(futures):
            cmd = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                print(f'{cmd} generated an exception: {exc}')
            else:
                results.append(result)
                print(f'Command: {result[0]}, Output: {result[1]}')

    # Démonstration que le programme principal continue de s'exécuter
    print("Le programme principal continue de fonctionner pendant que les commandes s'exécutent.")

if __name__ == '__main__':
    main()
