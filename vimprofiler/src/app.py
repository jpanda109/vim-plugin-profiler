# user-defined imports
from .modes import regurgitate
from .modes import startup
from .lib import wrappers


@wrappers.safe_exc
def main(screen, working_path):

    """ handles mode switching """

    y, x = screen.getmaxyx()
    commands = ['q: Quit', '1: Regurgitate', '2: Startup']

    mode = 1
    while mode != 0:
        # print the base commands (quit and modes)
        screen.clear()
        prev_col = 0
        for i in range(len(commands)):
            col = 0 if i == 0 else len(commands[i - 1]) + 4
            col += prev_col
            screen.addstr(y - 1, col, commands[i])
            prev_col = col
        # switch modes
        if mode == 1:
            regurgitate_mode = regurgitate.RegurgitateMode(screen, working_path)
            mode = regurgitate_mode.main()
        elif mode == 2:
            startup_mode = startup.StartupMode(screen, working_path)
            mode = startup_mode.main()
