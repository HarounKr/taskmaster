class SimpleCompleter:
    def __init__(self, options):
        self.options = options;
    
    def complete(self, text, state):
        if state < len(self.options):
            if text:
                self.matches = [x for x in self.options if x.startswith(text)]
            else:
                self.matches = self.options[:]
        try:
            response = self.matches[state] + " "
            del self.matches
        except IndexError:
            response = None
        return response