import socket


class Neighbor:
    def __init__(self, server_id, ip, port, cost):
        self.id = server_id
        self.ip = ip
        self.port = port
        self.cost = cost
        self._missed_updates = 0
        self._connection = None
        self._is_down = True

    @property
    def missed_updates(self):
        return self._missed_updates

    @missed_updates.setter
    def missed_updates(self, value):
        if value < 0:
            raise ValueError("Missed updates count cannot be negative.")
        self._missed_updates = value

    def increment_missed_updates(self):
        self._missed_updates += 1

    def reset_missed_updates(self):
        self._missed_updates = 0

    @property
    def connection(self):
        return self._connection

    @connection.setter
    def connection(self, value):
        if not isinstance(value, socket.socket) and value is not None:
            raise ValueError("Connection must be a socket instance or None.")
        self._connection = value
        print(f"connection established on {self.id} using setter")

    @property
    def is_down(self):
        return self._is_down

    def connect(self):
        print("connecting")
        try:
            print(self._connection)
            if self._connection is not None:
                raise RuntimeError("A connection already exists.")
            self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._connection.connect((self.ip, self.port))
            self._is_down = False
        except socket.error:
            self._connection.close()
            self._connection = None
            self._is_down = True
            print(f"Failed to connect to neighbor {self.id}")

    def close_connection(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            self._is_down = True

    def send(self, message):
        try:
            if self._connection is None:
                raise ValueError("No connection exists")
            self._connection.send(message)
        except socket.error as e:
            print(f"Error sending routing update to {self.id}: {e}")
