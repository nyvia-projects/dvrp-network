class CommandRegistry:
    def __init__(self):
        self.commands = {}

    def register(self, name, command):
        self.commands[name] = command

    def get_command(self, name):
        return self.commands.get(name)


command_registry = CommandRegistry()
