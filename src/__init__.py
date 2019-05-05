
# global funcion for non verbose printing
_verbose = False


def verbose(*args, **kwargs):
    if _verbose:
        print(*args, **kwargs)
