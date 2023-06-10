from commands.command_registry import command_registry


def register_command(name):
    def decorator(cls):
        command_registry.register(name, cls)
        return cls
    return decorator
