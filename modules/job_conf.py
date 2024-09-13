class JobConf:
    def __init__(self, name, conf):
        self.name = name
        self.numprocs = 1
        self.umask = 22
        self.autostart = True
        self.workingdir = "/home"
        self.autorestart = "unexpected"
        self.exitcodes = [0]
        self.startretries = 3
        self.starttime = 1
        self.stopsignal = "TERM"
        self.stoptime = 10
        self.env: dict = {}
        for key, value in conf.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if type(sub_value) is int:
                        sub_value = str(sub_value)
                    self.env[sub_key] = sub_value
            else:
                setattr(self, key, value)
        
    @property
    def getValues(self):
        return self.__dict__
    
    def __repr__(self):
        conf = [f'{key} : {getattr(self, key)}' for key in self.__dict__]
        return ('\n').join(conf)