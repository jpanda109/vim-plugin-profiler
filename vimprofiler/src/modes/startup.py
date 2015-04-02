import logging


logging.basicConfig(filename='logging_stuff.log', level=logging.DEBUG)


def _exit_mode(threads, screen):

    """ gracefully clean up everything this mode was doing """

    pass


def main(screen):
    y, x = screen.getmaxyx()
