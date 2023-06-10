from commands.base_command import Command


class PacketsCommand(Command):
    def __init__(self, *args):
        super().__init__(*args)

    def execute(self):
        print(self.server.num_packets)
        self.server.num_packets = 0
