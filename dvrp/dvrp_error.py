class DVRPError(Exception):
    def __init__(self, message: str):
        self.message = message


class TopologyFileError(DVRPError):
    def __init__(self, message: str = None):
        default_message = "Error reading topology file"
        super().__init__(default_message + (":\n\t " + message if message else ""))
        self.name = "InvalidTopologyFileError"


class InvalidNumServersError(TopologyFileError):
    pass


class InvalidNumNeighborsError(TopologyFileError):
    pass


class InvalidServerInfoError(TopologyFileError):
    pass


class InvalidNeighborInfoError(TopologyFileError):
    pass


class InvalidArgumentsError(DVRPError):
    def __init__(self, message: str = None):
        default_message = "Invalid argument(s)"
        super().__init__(default_message + (":\n\t " + message if message else ""))
        self.name = "InvalidArgumentsError"

