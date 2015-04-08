import curses
import os
from src.lib import utils
import src.app as app
# from .src import app


if __name__ == "__main__":

    """ simple where the curses screen and working path are set """

    myscreen = curses.initscr()
    curses.start_color()
    myscreen.nodelay(1)
    try:
        curses.noecho()
        curses.curs_set(0)

        exc = app.main(myscreen, working_path)
    finally:
        curses.echo()
        curses.endwin()

    if exc is not None:
        print(exc)
