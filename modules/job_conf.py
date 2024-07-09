from pydantic import BaseModel

class JobConf:
    def __init__(self, config, name):
        self.name = name
        self.is_started: bool = False
        self.env: dict = dict()
        self.pid: int = int()
        for key, value in config.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    self.env[sub_key] = sub_value
            else:
                setattr(self, key, value)

    @property
    def pid(self):
        return self._pid
    
    @pid.setter
    def pid(self, value):
        if value < 0:
            raise ValueError("PID cannot be negative")
        self._pid = value
        
    @property
    def getValues(self):
        return self.__dict__
    
    def __repr__(self):
        conf = [f'{key} : {getattr(self, key)}' for key in self.__dict__]
        return ('\n').join(conf)