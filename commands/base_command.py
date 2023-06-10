class Command:
    def __init__(self, server, *args):
        self.server = server
        self.args = args

    def execute(self):
        raise NotImplementedError("Subclasses must implement this method.")