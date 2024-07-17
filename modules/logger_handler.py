try:
    import logging
except ImportError as e:
    raise ImportError(f"Module import failed: {e}")

class LoggerHandler:
    def __init__(self, filename: str):
     
        self.logger = logging.getLogger('logger')
        self.logger.setLevel(logging.DEBUG)
       
        log_format = '%(asctime)s - %(levelname)s: %(message)s'
        if not self.logger.handlers:
            # Configuration du gestionnaire de fichier
            file_handler = logging.FileHandler(filename, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Configuration du gestionnaire de console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def log(self, message: str, level: str):
        if level == 'info':
            self.logger.info(message)
        elif level == 'error':
            self.logger.error(message)