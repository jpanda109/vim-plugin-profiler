import threading

# user-defined imports
from .modes import regurgitate
from .modes import startup
from .lib import wrappers


@wrappers.safe_exc
def main(screen, working_path):

    """ Handles mode switching """

    y, x = screen.getmaxyx()
    commands = ['q: Quit', '1: Regurgitate', '2: Startup']
    screen_lock = threading.RLock()

    next_mode = 1

    while next_mode != 0:

        # Print the command options
        screen.clear()
        prev_col = 0
        for i in range(len(commands)):
            col = 0 if i == 0 else len(commands[i - 1]) + 4
            col += prev_col
            screen.addstr(y - 2, col, commands[i])
            prev_col = col

        # Switch modes
        if next_mode == 1:
            mode = regurgitate.RegurgitateMode(screen, working_path, screen_lock)
        elif next_mode == 2:
            mode = startup.StartupMode(screen, working_path, screen_lock)
        else:
            mode = regurgitate.RegurgitateMode(screen, working_path, screen_lock)

        next_mode = mode.run()
