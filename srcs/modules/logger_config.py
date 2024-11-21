try:
    from modules.logger_handler import LoggerHandler
    import os, sys
except ImportError as e:
    raise ImportError(f"Module import failed: {e}")

try:
    log_filename = "/tmp/taskmaster/taskmaster.log"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    logger = LoggerHandler(log_filename)
except OSError as e:
    sys.stderr.write(f'unexpected error occurred in function [ main ] : {e}')