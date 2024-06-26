from modules.JobConf import JobConf
from pathlib import Path
import yaml

if __name__ == '__main__':
    jobs = dict()
    actual_path = str(Path().resolve())
    fileconf_path = actual_path[0:actual_path.rfind('/')] + '/conf/conf.yml'
    try:
        with open(fileconf_path, 'r') as file:
            yaml_content = yaml.safe_load(file)
            for key, value in yaml_content.items():
                jobConf = JobConf(value, key)
                jobs[key] = jobConf
    except Exception as error:
        print(error)