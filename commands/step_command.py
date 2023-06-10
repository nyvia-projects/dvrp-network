from commands.base_command import Command


class StepCommand(Command):
    def __init__(self, *args):
        super().__init__(*args)

    def execute(self):
        self.server.send_routing_update()
