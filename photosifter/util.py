import os

# Get absolute path to credentials folder
current = os.path.dirname(os.path.realpath(__file__))
AUTH_BASE = os.path.normpath(os.path.join(current, "auth"))

# global funcion for non verbose printing
enable_verbose = False


def verbose(*args, **kwargs):
    if enable_verbose:
        print(*args, **kwargs)
