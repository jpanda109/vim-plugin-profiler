import logging
import os
import shutil

from ..lib import utils


logging.basicConfig(filename='logging_stuff.log', level=logging.DEBUG)


class StartupMode(object):

    def __init__(self, screen, working_path):
        self.screen = screen
        self.working_path = working_path
        self.all_plugins = self.get_plugins()
        self.selected_line = 0
        self.exit_event = utils.ValueEvent()

    def main(self):
        y, x = self.screen.getmaxyx()

        for i, plugin in enumerate(self.all_plugins):
            self.screen.addstr(i, 0, plugin)
        self.screen.refresh()

        self.exit_event.wait()
        return self.exit_event.get_value()

    @staticmethod
    def get_plugins():
        vimrc_path = os.path.expanduser('~/.vim/.vimrc')
        with open(vimrc_path, 'r') as vimrc:
            plugins = []
            begin_flag = False
            for line in vimrc:
                if line.rstrip() == 'call vundle#begin()':
                    begin_flag = True
                if line.rstrip() == 'call vundle#end()':
                    break
                if begin_flag:
                    if line.startswith('Plugin'):
                        plugins.append(line.split()[1])
        return plugins
