# user-defined imports
from .modes import regurgitate
from .lib import wrappers


@wrappers.safe_exc
def main(screen, working_path):

    """ handles mode switching """

    y, x = screen.getmaxyx()
    commands = ['q: Quit', '1: Regurgitate']

    modes = {
        1: regurgitate.main
    }

    mode = 1
    while mode != 0:
        # print the base commands (quit and modes)
        screen.clear()
        for i in range(len(commands)):
            col = 0 if i == 0 else len(commands[i - 1]) + 4
            screen.addstr(y - 1, col, commands[i])
        # switch modes
        mode = modes[mode](screen, working_path)
