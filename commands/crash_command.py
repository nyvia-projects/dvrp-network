from commands.base_command import Command


class CrashCommand(Command):
    def __init__(self, server, *args):
        super().__init__(server, *args)

    def execute(self):
        for neighbor in self.server.neighbors:
            neighbor.close_connection()
