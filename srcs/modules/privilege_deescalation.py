import pwd, os, getpass, sys

def priv_deescalation(target_user ,proc: str):
    try:
        actual_uid = os.getuid()
        if actual_uid == 0:
            target_user_info = pwd.getpwnam(target_user)
            target_uid = target_user_info.pw_uid
            target_gid = target_user_info.pw_gid
                
                # Change le groupe effectif
            os.setgid(target_gid)
                
                # Change l'utilisateur effectif
            os.setuid(target_uid)
    except OSError as e:
        sys.stderr.write(f"{proc}: error at priv_deescalation\n")