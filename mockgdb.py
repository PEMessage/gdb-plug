import sys


class GdbCommandError(Exception):
    pass


class GdbMock:
    def execute(self, command, from_tty=False, to_string=False):
        print(f"[mockgdb] Executing command: {command}")
        if to_string:
            return "mock output"
        return None

    def __getattr__(self, name):
        # Return a dummy function for any undefined method
        def dummy_method(*args, **kwargs):
            print("[mockgdb] Called unimplemented method:" +
                  f"{name} with args: {args}, kwargs: {kwargs}")
            return None
        return dummy_method


# Create a singleton instance
gdb = GdbMock()

# For Python's module system
sys.modules[__name__] = gdb
