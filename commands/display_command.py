from commands.base_command import Command


class DisplayCommand(Command):
    def __init__(self, *args):
        super().__init__(*args)

    def execute(self):
        # Print the routing table
        print("Routing table for router", self.server.id)
        print("Destination\tCost\tNext Hop\tIP\t\tPort")
        for dest, info in self.server.routing_table.items():
            print(
                f"{dest}\t\t{info['cost']}\t{info['next_hop']}\t{info['ip']}\t{info['port']}"
            )
