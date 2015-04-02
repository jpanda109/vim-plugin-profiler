import logging
import os

from ..lib import utils


logging.basicConfig(filename='logging_stuff.log', level=logging.DEBUG)


def _exit_mode(threads, screen):

    """ gracefully clean up everything this mode was doing """

    pass


def main(screen, working_path):
    y, x = screen.getmaxyx()
    vimrc_path = os.path.expanduser('~/.vim/.vimrc')
    with open(vimrc_path, 'r') as vimrc:
        plugins = []
        begin_flag = False
        for line in vimrc:
            if line.rstrip() == 'call vundle#begin()':
                begin_flag = True
            if begin_flag:
                if line.rstrip().startswith('Plugin'):
                    plugins.append(line.split()[1])
    for i, plugin in enumerate(plugins):
        screen.addstr(i, 0, plugin)
    screen.refresh()

    exit_event = utils.ValueEvent()
    exit_event.wait()
    return exit_event.get_value()
