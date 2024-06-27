class JobConf:
    def __init__(self, config, name):
        self.name = name
        self.env = dict()
        self.pid = int()
        for key, value in config.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    self.env[sub_key] = sub_value
            else:
                setattr(self, key, value)

    def getValues(self):
        for key in self.__dict__:
            print(key)
        return self.__dict__
    
    def setPid(self, pid: int):
        self.pid = pid
    
    def __repr__(self):
        conf = [f'{key} : {getattr(self, key)}' for key in self.__dict__]
        return ('\n').join(conf)