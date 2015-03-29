import curses
import threading
import queue
import sys
from functools import wraps


def safe_curses(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except:
            pass
    return wrapper


def process_input(input_queue, screen):
    while True:
        keypress = screen.getkey()
        input_queue.put(keypress)


@safe_curses
def main(screen):
    screen.border(0)
    screen.addstr(12, 25, "Python curses in action!")
    screen.refresh()

    input_queue = queue.Queue()
    input_thread = threading.Thread(target=process_input,
                                    args=(input_queue, screen), daemon=True)
    input_thread.start()
    while True:
        if not input_queue.empty():
            keypress = input_queue.get()
            if keypress == 'q' or keypress == 'Q':
                break
            screen.addstr(30, 30, keypress)


if __name__ == "__main__":
    myscreen = curses.initscr()
    curses.noecho()

    main(myscreen)

    curses.echo()
    curses.endwin()
