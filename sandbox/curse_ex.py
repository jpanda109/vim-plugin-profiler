import curses


if __name__ == "__main__":
    myscreen = curses.initscr()

    dimensions = myscreen.getmaxyx()

    myscreen.border(0)
    myscreen.addstr(12, 25, "Python curses in action!")
    myscreen.refresh()
    myscreen.getch()

    curses.endwin()
