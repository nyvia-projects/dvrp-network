from commands.base_command import Command


class UpdateCommand(Command):
    def __init__(self, server, server_id1=None, server_id2=None, link_cost=None, *args):
        super().__init__(server, *args)
        self.server_id1 = server_id1
        self.server_id2 = server_id2
        self.link_cost = link_cost

    def execute(self):
        if self.server_id1 and self.server_id2 and self.link_cost:
            neighbor_id = self.server_id2 if self.server_id1 == self.server.id else self.server_id1
            self.server.update_link_cost(neighbor_id, self.link_cost)
        else:
            print("Please provide valid server-ID1, server-ID2, and Link Cost")
