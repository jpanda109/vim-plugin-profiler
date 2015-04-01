import curses
import os
import app.app as app


if __name__ == "__main__":
    working_path = os.path.dirname(os.path.abspath(__file__))
    myscreen = curses.initscr()
    myscreen.nodelay(1)
    try:
        curses.noecho()
        curses.curs_set(0)

        exc = app.main(myscreen, working_path)
        # exc = main(myscreen)
    finally:
        curses.echo()
        curses.endwin()

    if exc is not None:
        print(exc)
