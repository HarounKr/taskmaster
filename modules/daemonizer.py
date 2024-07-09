import sys
import os
import atexit

stdin = '/dev/null'
stdout = '/dev/null'
stderr = '/dev/null'

class Daemonizer:
    def __init__(self):
        try:
            pid = os.fork()
            if pid > 0:
                # Quitter le premier parent.
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"fork #1 failed: {e.errno} ({e.strerror})\n")
            sys.exit(1)

        # Se détacher de l'environnement du parent
        os.chdir("/")
        os.setsid()
        os.umask(0)
        # second fork
        try:
            pid = os.fork()
            if pid > 0:
                # quitter le second parent.
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"fork #2 failed: {e.errno} ({e.strerror})\n")
            sys.exit(1)

        # Redirection des descripteurs de fichier standard
        sys.stdout.flush()
        sys.stderr.flush()
        with open(stdin, 'rb', 0) as si:
            os.dup2(si.fileno(), sys.stdin.fileno())
        with open(stdout, 'ab', 0) as so:
            os.dup2(so.fileno(), sys.stdout.fileno())
        with open(stderr, 'ab', 0) as se:
            os.dup2(se.fileno(), sys.stderr.fileno())