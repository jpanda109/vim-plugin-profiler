# STL imports
import logging

# user-defined imports
from .modes import regurgitate
from .lib import wrappers


logging.basicConfig(filename='logging_stuff.log', level=logging.DEBUG)


modes = {
    1: regurgitate.main
}


@wrappers.safe_exc
def main(screen, working_path):
    mode = 1
    while mode != 0:
        modes[mode](screen, working_path)
        #  regurgitate.main(screen, working_path)
