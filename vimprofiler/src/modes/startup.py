import logging
import queue
import threading
import curses
import os
import subprocess

from ..modes import abstract_mode

from ..lib import utils


logging.basicConfig(filename='logging_stuff.log', level=logging.DEBUG)


class StartupMode(abstract_mode.Mode):

    def __init__(self, screen, working_path):
        """
        initialize mode to be run by main application
        :param screen: screen that mode is working with
        :param working_path: working path of where youw ant to store stuff
        :return:
        """
        self.screen = screen
        self.working_path = working_path
        self.selected_line = 0  # highlights line selected by user (for toggling plugins)
        self.threads = []  # threads being managed by mode
        self.exit_event = utils.ValueEvent()  # signals when to terminate program
        self.change_event = threading.Event()  # signals change due to user input
        self.analysis_event = threading.Event()  # signals an analysis request was sent
        self.vimrc_path = os.path.expanduser('~/.vim/.vimrc')  # path to user's vimrc
        self.all_plugins = self.get_plugins(self.vimrc_path)  # all plugins originally sourced by user
        self.plugin_statuses = [True] * len(self.all_plugins)  # indicates which plugins currently sourced
        self.status_lock = threading.Lock()  # lock for modifying and viewing statuses
        self.startup_lock = threading.Lock()  # lock for startup analysis (file modification)
        self.analysis_queue = queue.Queue()  # atomic queue containing lines from --startuptime command

    def run(self):
        """
        public inherited method that all methods must have to run
        :return: the next mode, which is returned when the mode if done running, based on
            exit_event
        """
        y, x = self.screen.getmaxyx()

        for i, plugin in enumerate(self.all_plugins):
            self.screen.addstr(i, 2, plugin)
        self.screen.refresh()

        self.threads.append(threading.Thread(target=self._process_input,
                                             daemon=True))
        self.threads.append(threading.Thread(target=self._display_to_screen,
                                             daemon=True))
        for thread in self.threads:
            thread.start()

        self.exit_event.wait()
        self._exit_mode()
        return self.exit_event.get_value()

    def _display_to_screen(self):
        """
        display plugins and their statuses along with cursor position, changes when
        change_event is set
        :return:
        """
        y, x = self.screen.getmaxyx()
        commands = ['j: Down', 'k: Up', 'c: Toggle', 's: Simulate']
        prev_col = 0
        for i in range(len(commands)):
            col = 0 if i == 0 else len(commands[i-1]) + 4
            col += prev_col
            self.screen.addstr(y - 2, col, commands[i])
            prev_col = col

        self.change_event.set()
        while not self.exit_event.is_set():
            if self.change_event.is_set():
                # deal with user input changes
                with self.status_lock:
                    for i, status in enumerate(self.plugin_statuses):
                        s = 'O' if status else 'X'
                        new_text = s + ' ' + self.all_plugins[i]
                        self.screen.addstr(i, 0, new_text)
                        self.screen.noutrefresh()
                    s = 'O' if self.plugin_statuses[self.selected_line] else 'X'
                new_text = s + ' ' + self.all_plugins[self.selected_line]
                self.screen.addstr(self.selected_line, 0, new_text, curses.A_STANDOUT)
                self.screen.noutrefresh()
                curses.doupdate()
                self.change_event.clear()
            if self.analysis_event.is_set():
                # deal with startup analysis requests
                while not self.analysis_queue.empty():
                    source_times = self.analysis_queue.get()
                for i in range(10):
                    self.screen.addstr(i + 10, 0, source_times[i])
                    self.screen.noutrefresh()
                curses.doupdate()
                self.analysis_event.clear()

    def _exit_mode(self):
        """
        clean up threads and other weird stuff
        :return:
        """
        for thread in self.threads:
            self.screen.clear()
            self.screen.addstr(0, 0, 'cleaning up')
            self.screen.refresh()
            thread.join()

    def _get_startup(self):
        """
        get startup information based on new vimrc
        :return:
        """
        vimrc_new_path = os.path.join(self.working_path, 'vimrc')

        # get valid plugins
        valid_plugins = []
        with self.status_lock:
            for i, p in enumerate(self.all_plugins):
                if self.plugin_statuses[i]:
                    valid_plugins.append('Plugin ' + p)

        # create process to open vim using --startuptime
        with self.startup_lock:
            with open(self.vimrc_path, 'r') as vimrc_orig:
                with open(vimrc_new_path, 'w') as vimrc_new:
                    for line in vimrc_orig:
                        if line.startswith('Plugin') and line.rstrip() not in valid_plugins:
                            continue
                        else:
                            vimrc_new.write(line)
            startup_file_path = os.path.join(self.working_path, 'startup.log')
            vim_command = 'vim -u ' + vimrc_new_path + ' --startuptime ' + startup_file_path
            args = ['gnome-terminal', '-e', vim_command]
            proc = subprocess.Popen(args).pid
            os.waitid(os.P_PID, int(proc), os.WEXITED)

            # check if startup file successfully made
            while not os.path.exists(startup_file_path):
                pass
            while True:
                with open(startup_file_path, 'r') as startup_file:
                    for line in startup_file:
                        pass
                    if 'VIM STARTED' in line:
                        break
            proc = (subprocess.Popen(['pgrep', '-f', vim_command[:7]],
                                     stdout=subprocess.PIPE)
                              .stdout.read().decode('utf-8').rstrip())
            os.kill(int(proc), 9)
            swap_file_path = os.path.join(self.working_path, '.swp')
            try:
                os.remove(swap_file_path)
            except OSError:
                pass

            # gather source info from startuptime file
            source_times = []
            with open(startup_file_path, 'r') as startup_file:
                for line in startup_file:
                    logging.debug(line.rsplit(' '))
                    try:
                        float(line.rsplit(' ')[2])
                    except (ValueError, IndexError):
                        continue
                    source_times.append(line)

            # sort and place info into analysis queue
            source_times.sort(key=lambda s_line: float(s_line.split(' ')[2]))
            self.analysis_queue.put(source_times)
            self.analysis_event.set()
            os.remove(vimrc_new_path)
            os.remove(startup_file_path)

    def _process_input(self):
        """
        get keypresses from curses.screen and act accordingly
        :return:
        """
        while not self.exit_event.is_set():
            try:
                keypress = self.screen.getkey()
                if keypress == 'q' or keypress == 'Q':  # quit program
                    self.exit_event.set(0)
                elif keypress == '1':  # switch to mode 1
                    self.exit_event.set(1)
                elif keypress == '2':  # switch to mode 2
                    self.exit_event.set(2)
                elif keypress == 'k':  # move selected line up
                    if self.selected_line != 0:
                        self.selected_line -= 1
                        self.change_event.set()
                elif keypress == 'j':  # move selected line down
                    if self.selected_line != len(self.all_plugins) - 1:
                        self.selected_line += 1
                        self.change_event.set()
                elif keypress == 'c':  # toggle selected plugin
                    with self.status_lock:
                        self.plugin_statuses[self.selected_line] = not self.plugin_statuses[self.selected_line]
                    self.change_event.set()
                elif keypress == 's':  # send analysis request for currently selected plugins
                    self._get_startup()
                logging.debug(keypress)
            except curses.error:
                pass

    @staticmethod
    def get_plugins(vimrc_path):
        """
        static method to retrieve plugins from vimrc file, assuming vundle based
        :param vimrc_path: path to original vimrc
        :return: list of plugins
        """
        with open(vimrc_path, 'r') as vimrc:
            plugins = []
            begin_flag = False
            for line in vimrc:
                if line.rstrip() == 'call vundle#begin()':
                    begin_flag = True
                if line.rstrip() == 'call vundle#end()':
                    break
                if begin_flag:
                    if line.startswith('Plugin') and 'Vundle' not in line:
                        plugins.append(line.split()[1])
        return plugins
