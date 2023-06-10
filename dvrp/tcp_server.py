import struct
from select import select
import socket
import sys
import time
from commands.decorators import register_command
from commands.update_command import UpdateCommand
from commands.step_command import StepCommand
from commands.packets_command import PacketsCommand
from commands.display_command import DisplayCommand
from commands.disable_command import DisableCommand
from commands.crash_command import CrashCommand

from commands.command_registry import command_registry
from dvrp.neighbor import Neighbor


class TCPServer:
    __instance = None

    def __init__(self, id: int, ip: str, port: int, interval: int):
        self.interval = interval
        self.id = id
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip, port))
        self.socket.listen()
        # Maintain a list of incoming connections, starting with the server socket
        self.connections = [self.socket]
        self.neighbors = []
        self.routing_table = {}
        self.last_executed = time.time()
        self.num_packets = 0
        print(f"Connection started, listening on {self.ip}:{self.port}")

    @staticmethod
    def getTCPServer(server_info: dict, interval: int, servers: list, neighbors: list):
        if TCPServer.__instance is None:
            id = server_info["id"]
            ip = server_info["ip"]
            port = server_info["port"]
            TCPServer.__instance = TCPServer(id, ip, port, interval)
            TCPServer.__instance.add_connections(servers, neighbors)
            TCPServer.__instance.create_routing_table(servers, neighbors)
            TCPServer.register_commands()
        else:
            raise Exception("A TCPServer instance has already been created.")
        return TCPServer.__instance

    def create_routing_table(self, servers: list, neighbors: list):
        infinity = 65535

        # Initialize the routing table with all routers and set the cost to infinity
        self.routing_table[self.id] = {
            "ip": self.ip,
            "port": self.port,
            "cost": 0,
            "next_hop": self.id
        }
        for server in servers:
            if server["id"] != self.id:
                self.routing_table[server['id']] = {
                    "ip": server['ip'],
                    "port": server['port'],
                    "cost": infinity,
                    "next_hop": None
                }

        # Update the routing table with the directly connected neighbors
        for neighbor in neighbors:
            neighbor_info = next(
                (r for r in servers if r["id"] == neighbor['id2']), None
            )
            if neighbor_info:
                self.routing_table[neighbor['id2']] = {
                    "ip": neighbor_info['ip'],
                    "port": neighbor_info['port'],
                    "cost": neighbor['cost'],
                    "next_hop": neighbor['id2']
                }

        # Print the routing table
        print("Routing table for router", self.id)
        print("Destination\tCost\tNext Hop\tIP\t\tPort")
        print(f"{self.id}\t\t0\t{self.id}\t{self.ip}\t{self.port}")
        for dest, info in self.routing_table.items():
            print(
                f"{dest}\t\t{info['cost']}\t{info['next_hop']}\t{info['ip']}\t{info['port']}"
            )

    def send_routing_update(self):
        # Prepare the routing update packet
        num_update_fields = len(self.routing_table)
        packet_format = f"!H H 4s {num_update_fields * 12}s"
        server_ip = socket.inet_aton(self.ip)
        server_port = self.port

        # Fill in the routing table information
        routing_data = b""
        for dest, info in self.routing_table.items():
            dest_ip = socket.inet_aton(info['ip'])
            dest_port = info['port']
            dest_id = dest
            cost = info['cost']
            routing_data += struct.pack("!4s H 2s H H", dest_ip, dest_port, b'\x00\x00', dest_id, int(cost))

        # Create the binary message
        message = struct.pack(
            packet_format, num_update_fields, server_port, server_ip, routing_data
        )
        # Send the message to each neighbor
        for neighbor in self.neighbors:
            if not neighbor.is_down:
                neighbor.send(message)

    def decode_routing_update_packet(self, packet):
        # Unpack the packet header
        num_update_fields, server_port, server_ip = struct.unpack("!H H 4s", packet[:8])
        packet = packet[8:]

        # Convert the server IP address to a string
        server_ip = socket.inet_ntoa(server_ip)

        # Iterate over the routing table entries and unpack each one
        routing_table = []
        for i in range(num_update_fields):
            dest_ip, dest_port, _, dest_id, cost = struct.unpack("!4s H 2s H H", packet[:12])
            packet = packet[12:]

            # Convert the destination IP address to a string
            dest_ip = socket.inet_ntoa(dest_ip)

            # Add the routing table entry to the dictionary
            routing_table.append({'id': dest_id, 'ip': dest_ip, 'port': dest_port, 'cost': cost})

        # Return a tuple containing the server IP, server port, and routing table
        return server_ip, server_port, routing_table

    def add_connections(self, servers: list, neighbors: list):
        neighbor_servers = {n['id2']: {'cost': n['cost'], **(next((s for s in servers if s['id'] == n['id2']), None))}
                            for n in neighbors}

        for server_id, details in neighbor_servers.items():
            ip = details["ip"]
            port = details["port"]
            cost = details["cost"]
            new_neighbor = Neighbor(server_id, ip, port, cost)
            self.neighbors.append(new_neighbor)
            new_neighbor.connect()


    @staticmethod
    def register_commands():
        register_command("update")(UpdateCommand)
        register_command("step")(StepCommand)
        register_command("packets")(PacketsCommand)
        register_command("display")(DisplayCommand)
        register_command("disable")(DisableCommand)
        register_command("crash")(CrashCommand)

    def get_command(self, command_string):
        command_parts = command_string.split()
        command_name = command_parts[0].lower()
        command_args = command_parts[1:]

        command_cls = command_registry.get_command(command_name)

        if command_cls is None:
            raise ValueError(f"Invalid command: {command_name}")

        return command_cls(self, *command_args)

    def periodic_update(self):
        for neighbor in self.neighbors:
            if not neighbor.is_down:
                neighbor.increment_missed_updates()
                if neighbor.missed_updates >= 3:
                    neighbor.close_connection()
        self.send_routing_update()

    def process_routing_update(self, sender_ip, sender_port, sender_routing_table):
        # Find the sender's ID and cost
        sender_id = None
        sender_cost = None
        for neighbor in self.neighbors:
            if neighbor.ip == sender_ip and neighbor.port == sender_port:
                sender_id = neighbor.id
                sender_cost = neighbor.cost
                break

        if sender_id is None:
            print(f"Could not find sender {sender_ip}:{sender_port} in neighbors")
            return

        for neighbor in self.neighbors:
            if neighbor.id == sender_id:
                neighbor.reset_missed_updates()
                if neighbor.is_down:
                    neighbor.connect()
                break

        # Update the routing table using the received routing table
        self.update_routing_table(sender_id, sender_cost, sender_routing_table)
        print(f"RECEIVED A MESSAGE FROM SERVER {sender_id}")

    def update_routing_table(self, sender_id, sender_cost, routing_update):
        # Check if the sender is a direct neighbor
        if sender_id not in self.routing_table:
            print(f"Sender {sender_id} not in the routing table")
            return

        # Update the routing table for the sender
        self.routing_table[sender_id]['cost'] = sender_cost
        self.routing_table[sender_id]['next_hop'] = sender_id

        # Apply the Bellman-Ford algorithm
        for entry in routing_update:
            dest_id = entry['id']
            dest_cost = entry['cost']

            if dest_id == self.id:
                continue

            if dest_id not in self.routing_table:
                self.routing_table[dest_id] = {
                    'ip': entry['ip'],
                    'port': entry['port'],
                    'cost': sender_cost + dest_cost,
                    'next_hop': sender_id
                }
            else:
                new_cost = sender_cost + dest_cost
                current_cost = self.routing_table[dest_id]['cost']

                if new_cost < current_cost:
                    self.routing_table[dest_id]['cost'] = new_cost
                    self.routing_table[dest_id]['next_hop'] = sender_id

    def update_link_cost(self, neighbor_id, cost):
        for neighbor in self.neighbors:
            if neighbor.id == neighbor_id:
                neighbor.cost = cost
                break

        # Prepare the routing update packet
        packet_format = f"!H H 4s 12s"
        server_ip = socket.inet_aton(self.ip)
        server_port = self.port

        # Fill in the routing table information
        routing_data = b""
        dest_ip, dest_port, _ = self.routing_table[neighbor_id]
        dest_ip = socket.inet_aton(dest_ip)
        routing_data += struct.pack("!4s H 2s H H", dest_ip, dest_port, b'\x00\x00', neighbor_id, int(cost))

        # Create the binary message
        message = struct.pack(
            packet_format, 1, server_port, server_ip, routing_data
        )
        # Send the message to each neighbor
        for neighbor in self.neighbors:
            if neighbor.id == neighbor_id:
                if not neighbor.is_down:
                    neighbor.send(message)

    def mainloop(self):
        print("Listening...")
        # Prompt the user for input
        print(">> ", end="")
        while True:
            sys.stdout.flush()
            # Calculate the remaining time until the next execution of the periodic_function
            remaining_time = self.interval - (time.time() - self.last_executed)
            # Ensure that the remaining time is non-negative
            remaining_time = max(remaining_time, 0)

            # Use the remaining time as the timeout value for select
            rlist, _, _ = select(self.connections +
                                 [sys.stdin], [], [], remaining_time)
            for r in rlist:
                if r == self.socket:
                    # Accept the new connection and add it to the list of connections
                    conn, address = self.socket.accept()
                    self.connections.append(conn)
                    # Print a message to indicate that a new connection has been established
                    print(f"The connection to peer {address} is successfully established;")
                elif r == sys.stdin:
                    # Process the user's command
                    command_string = sys.stdin.readline().strip()
                    try:
                        command = self.get_command(command_string)
                        command.execute()
                    except ValueError as e:
                        print(e)
                else:
                    # TODO this will need to be reworked probably to handle the different types of messages
                    # Receive a message from the connection and display it
                    try:
                        # Receive a message from the connection and display it
                        data = r.recv(1024)
                    except ConnectionResetError:
                        data = None

                    host, port = r.getpeername()
                    if not data:
                        print(r)
                        # If the connection has been closed, remove it from the list of connections and print a message
                        self.connections.remove(r)
                        r.close()
                        print(f"Peer {host} terminates the connection")
                    else:
                        # If a message has been received, process it
                        self.num_packets += 1
                        sender_ip, sender_port, sender_routing_table = self.decode_routing_update_packet(data)
                        self.process_routing_update(sender_ip, sender_port, sender_routing_table)
                        sender_id = -1

                # Prompt the user for input
                print(">> ", end="")

            # Check if it's time to execute the periodic_function
            if time.time() - self.last_executed >= self.interval:
                self.periodic_update()
                self.last_executed = time.time()
