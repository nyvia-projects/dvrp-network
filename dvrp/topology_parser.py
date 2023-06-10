import socket
import re
from dvrp.dvrp_error import *


def is_valid_ipv4(ip_address: str):
    """
    Checks if the given string is a valid IPv4 address.

    Args:
        ip_address (str): The IP address to check.

    Returns:
        bool: True if the IP address is valid, False otherwise.
    """
    try:
        socket.inet_pton(socket.AF_INET, ip_address)
        return True
    except socket.error:
        return False


def is_valid_port(port: int):
    """
    Checks if the given port number is valid (i.e., within the range 1024 to 65535).

    Args:
        port (int): The port number to check.

    Returns:
        bool: True if the port is valid, False otherwise.
    """

    return 1024 <= port <= 65535


def parse_int(value: int, line_number: int, error_class: DVRPError):
    try:
        return int(value)
    except ValueError:
        raise error_class(f"Invalid integer value at line {line_number}")


def is_valid_port(port: int):
    return 1024 <= port <= 65535


def read_topology(lines: list):
    num_servers = int(lines[0].strip())
    num_neighbors = int(lines[1].strip())

    if num_servers <= 1:
        raise InvalidNumServersError("num_servers must be greater than 1")

    if num_neighbors >= num_servers:
        raise InvalidNumNeighborsError("num_neighbors must be less than num_servers")

    # validate server information
    server_info_lines = lines[2 : 2 + num_servers]
    servers = []
    for i, server_line in enumerate(server_info_lines, start=3):
        parts = server_line.strip().split()
        if len(parts) != 3:
            raise InvalidServerInfoError(f"Invalid server information at line {i}")
        server_id = int(parts[0])
        server_ip = parts[1]
        server_port = int(parts[2])

        if not re.match(r"^(\d{1,3}\.){3}\d{1,3}$", server_ip) or not is_valid_ipv4(
            server_ip
        ):
            raise InvalidServerInfoError(f"Invalid IPv4 address at line {i}")

        if not is_valid_port(server_port):
            raise InvalidServerInfoError(
                f"Invalid server port at line {i}: (port must be within 1024-65535)"
            )

        servers.append({"id": server_id, "ip": server_ip, "port": server_port})

    # validate neighbor information
    neighbor_info_lines = lines[2 + num_servers :]
    neighbors = []
    for i, neighbor_line in enumerate(neighbor_info_lines, start=3 + num_servers):
        parts = neighbor_line.strip().split()
        if len(parts) != 3:
            raise InvalidNeighborInfoError(f"Invalid neighbor information at line {i}")
        id1 = int(parts[0])
        id2 = int(parts[1])
        cost = int(parts[2])

        if not (1 <= id1 <= num_servers and 1 <= id2 <= num_servers):
            raise InvalidNeighborInfoError("Invalid neighbor IDs")

        neighbors.append({"id1": id1, "id2": id2, "cost": cost})

    if len(neighbors) != num_neighbors:
        raise InvalidNeighborInfoError(
            f"Expected {num_neighbors} neighbor information but received {len(neighbors)}"
        )

    return servers, neighbors
