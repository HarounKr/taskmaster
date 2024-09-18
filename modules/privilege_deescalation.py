import pwd, os, getpass, sys

def priv_deescalation(proc: str):
    try:
        actual_uid = os.getuid()
        if actual_uid == 0:
            user = getpass.getuser()
            useruid = pwd.getpwnam(user).pw_uid
            os.setuid(useruid)
    except OSError as e:
        sys.stderr.write(f"{proc}: error at priv_deescalation\n")