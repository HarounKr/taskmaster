# Taskmaster

Taskmaster is a simple **job control** and **job monitoring** program, running in daemon mode. It allows you to launch and supervise one or more programs from a `conf.yml` configuration file.

---

## Prerequisites

- **Python 3** (recommended version 3.6+)
- **Configuration file**: a `conf.yml` file (provided in the `srcs/conf` directory)
- Required Python libraries (listed in `requirement.txt`)

---

## Installation and Configuration

1. **Clone the repository** and navigate to the project's root directory.
2. **Copy the configuration file** to `/tmp`:
   ```bash
   cp srcs/conf/conf.yml /tmp
   ```
3. **Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```
4. **Add the srcs directory to PYTHONPATH:**
```bash
export PYTHONPATH="$PYTHONPATH:./srcs"
```
5. **Install the dependencies**
```bash
python3 -m pip install -r requirement.txt
```
6. **Start the daemon:**
```bash
python3 srcs/server/taskmasterd.py
```
The server reads the configuration and manages the programs specified in conf.yml.  
7. **Start the client:**
```bash
python3 srcs/client/taskmasterctl.py
```
The client sends commands to the server to start/stop/restart jobs.

```bash
taskmasterctl> start ping
Request send to Daemon, waiting ..
The following task(s) have been successfully started: ping.
```