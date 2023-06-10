from commands.base_command import Command


class DisableCommand(Command):
    def __init__(self, server_id=None, *args):
        super().__init__(*args)
        self.server_id = server_id

    def execute(self):
        if self.server_id:
            print(f"Disabling link to {self.server_id}")
        else:
            print("Please provide valid server-ID")
