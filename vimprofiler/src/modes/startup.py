import logging
import threading
import curses
import os
import shutil

from ..modes import abstract_mode

from ..lib import utils


logging.basicConfig(filename='logging_stuff.log', level=logging.DEBUG)


class StartupMode(abstract_mode.Mode):

    def __init__(self, screen, working_path):
        self.screen = screen
        self.working_path = working_path
        self.all_plugins = self.get_plugins()
        self.current_plugins = self.all_plugins.copy()
        self.selected_line = 0
        self.threads = []
        self.exit_event = utils.ValueEvent()

    def run(self):
        y, x = self.screen.getmaxyx()

        for i, plugin in enumerate(self.all_plugins):
            self.screen.addstr(i, 2, plugin)
        self.screen.refresh()

        self.threads.append(threading.Thread(target=self._process_input,
                                             daemon=True))
        for thread in self.threads:
            thread.start()

        self.exit_event.wait()
        self._exit_mode()
        return self.exit_event.get_value()

    def get_next_mode(self):
        return self.exit_event.get_value()

    def _exit_mode(self):
        for thread in self.threads:
            self.screen.clear()
            self.screen.addstr(0, 0, 'cleaning up')
            self.screen.refresh()
            thread.join()

    def _process_input(self):
        while not self.exit_event.is_set():
            try:
                keypress = self.screen.getkey()
                if keypress == 'q' or keypress == 'Q':
                    self.exit_event.set(0)
                if keypress == '1':
                    self.exit_event.set(1)
                if keypress == '2':
                    self.exit_event.set(2)
            except curses.error:
                pass

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
