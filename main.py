import sys
import argparse
from dvrp import *


def process_topology(file_path: str):
    try:
        with open("topologies/" + file_path, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        raise DVRPError("Topology file not found.")

    try:
        server, neighbors = read_topology(lines)
        print(
            f"Validated topology, detected {len(server)} servers and {len(neighbors)} neighbors info"
        )
    except TopologyFileError as custom_error:
        raise DVRPError(
            f"Error processing topology file:\n\t {custom_error}"
        ) from custom_error
    except (IndexError, ValueError):
        raise DVRPError(
            "Error processing topology file:\n\t Check file syntax")

    return server, neighbors


def main():
    try:
        parser = argparse.ArgumentParser(
            description="A simple script that demonstrates handling flags in Python")

        parser.add_argument("-t", "--topology",
                            help="Output file path", required=True, type=str)
        parser.add_argument("-i", "--interval",
                            help="Input file path", required=True, type=int)

        args = parser.parse_args()

        file_path = args.topology
        interval = args.interval

        servers, neighbors = process_topology(file_path)
        tcp_server = TCPServer.getTCPServer(
            servers.pop(0), interval, servers, neighbors)

        # Print TCPServer attributes
        print(f"IP: {tcp_server.ip}")
        print(f"Port: {tcp_server.port}")
        print(f"Additional servers: {tcp_server.neighbors}")

        tcp_server.mainloop()

    except DVRPError as e:
        print(e.args[0])  # print the error message from the exception
        sys.exit(1)
    except Exception as e:
        print(f"An unknown error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
