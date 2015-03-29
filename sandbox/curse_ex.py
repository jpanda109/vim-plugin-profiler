import curses
import threading
import queue


def process_input(input_queue, screen):
    while True:
        keypress = screen.getkey()
        input_queue.put(keypress)

if __name__ == "__main__":
    myscreen = curses.initscr()

    dimensions = myscreen.getmaxyx()

    myscreen.border(0)
    myscreen.addstr(12, 25, "Python curses in action!")
    myscreen.refresh()

    input_queue = queue.Queue()
    input_thread = threading.Thread(target=process_input,
                                    args=(input_queue, myscreen), daemon=True)
    input_thread.start()
    while True:
        if not input_queue.empty():
            keypress = input_queue.get()
            if keypress == 'q' or keypress == 'Q':
                break
            myscreen.addstr(30, 30, keypress)

    curses.endwin()
