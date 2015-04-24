import curses
import os
import src.app as app


if __name__ == "__main__":

    """ Set the curses screen and working path """

    working_path = os.path.dirname(os.path.abspath(__file__))
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
