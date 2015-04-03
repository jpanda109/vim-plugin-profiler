import os
import logging
import threading
import queue
import subprocess
import time
import collections
import json
import sqlite3
import curses

from ..lib import utils
from ..modes import abstract_mode


logging.basicConfig(filename='logging_stuff.log', level=logging.DEBUG)
HERTZ = 250  # Clock Hertz of computer (shouldn't hard code but whatev)
env_command = {
    'ubuntu': 'gnome-terminal',
    'xubuntu': 'xfce4-terminal'
}
desktop_env = os.environ.get('DESKTOP_SESSION')


""" tasks to be run by threads"""


class RegurgitateMode(abstract_mode.Mode):

    def __init__(self, screen, working_path):

        """
        Initializes this mode
        :param screen: screen that you're working with
        :param working_path: path where things like plugin.vim is stored
        :return:
        """
        self.screen = screen
        self.working_path = working_path
        self.exit_event = utils.ValueEvent()
        self.interval = 1
        self.display_queue = queue.Queue()
        self.pipe_name = os.path.join(self.working_path, 'tmpfifo')
        self.proc = self.initialize_vim(self.working_path, self.pipe_name)
        self.threads = []

    def _calculate_cpu(self):

        """ calculate_cpu and send to display_queue
        """

        proc_file_name = '/proc/' + str(os.getpid()) + '/stat'
        time_file_name = '/proc/stat'
        utime_prev = 0
        stime_prev = 0
        cutime_prev = 0
        cstime_prev = 0
        with open(time_file_name, 'r') as time_file:
            time_stats = time_file.readline().split(' ')[2:]
        time_prev = sum(map(float, time_stats))
        time.sleep(self.interval)
        while not self.exit_event.is_set():
            with open(proc_file_name, 'r') as proc_file:
                stats = proc_file.readline().split(' ')
            with open(time_file_name, 'r') as time_file:
                time_stats = time_file.readline().split(' ')[2:]
            utime_next = float(stats[13])
            stime_next = float(stats[14])
            cutime_next = float(stats[15])
            cstime_next = float(stats[16])

            time_next = sum(map(float, time_stats))
            seconds = time_next - time_prev

            total_time = (utime_next - utime_prev) + (stime_next - stime_prev)
            total_time += (cutime_next - cutime_prev) + (cstime_next - cstime_prev)
            cpu_usage = 100 * ((total_time / HERTZ) / seconds)

            self.display_queue.put(cpu_usage)
            time.sleep(self.interval)

            utime_prev = utime_next
            stime_prev = stime_next
            cutime_prev = cutime_next
            cstime_prev = cstime_next
            time_prev = time_next

    def _display_to_screen(self):

        """
        display stuff from display_queue to screen
        :return:
        """

        y, x = self.screen.getmaxyx()
        display_deque = collections.deque(maxlen=y-4)
        while not self.exit_event.is_set():
            if not self.display_queue.empty():
                display_deque.append(self.display_queue.get())
                curses.setsyx(0, 0)
                for i, item in enumerate(display_deque):
                    self.screen.clrtoeol()
                    self.screen.addstr(i, 0, str(item)[:x-2])
                    self.screen.noutrefresh()
                curses.doupdate()

    def _load_commands(self):

        """
        get commands from vim process through pipe, and act accordingly
        :return:
        """

        try:
            os.remove('commands.db')
        except OSError:
            pass
        conn = sqlite3.connect('commands.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE commands (time, command)''')
        with open(self.pipe_name, 'r') as pipe:
            while not self.exit_event.is_set():
                line = pipe.readline()
                if line.rstrip() == '':
                    continue
                command = json.loads(line, encoding='utf-8')
                self.display_queue.put(command)
                c.execute('INSERT INTO commands VALUES (?,?)',
                          (command['time'], command['command']))
        conn.commit()
        conn.close()

    def _process_input(self):

        """
        thread that gets input from screen and acts accordingly
        :return:
        """

        while not self.exit_event.is_set():
            try:
                keypress = self.screen.getkey()
                logging.debug(keypress)
                if keypress == 'q' or keypress == 'Q':
                    self.exit_event.set(0)
                if keypress == '1':
                    self.exit_event.set(1)
                if keypress == '2':
                    self.exit_event.set(2)
            except curses.error:
                pass

    def _exit_mode(self):

        """
        gracefully clean up everything this mode was doing
        :return:
        """

        for thread in self.threads:
            self.screen.clear()
            self.screen.addstr(0, 0, 'cleaning up')
            self.screen.refresh()
            thread.join()
        try:
            os.kill(self.proc, 9)
        except OSError:
            pass
        try:
            os.remove(self.pipe_name)
        except OSError:
            pass

    def run(self):

        """ main function for this mode
        :return the mode that should be switched to
        """

        # display mode specific commands on line y - 2
        y, x = self.screen.getmaxyx()
        commands = ['a: Analyze', 'o: Open']
        for i in range(len(commands)):
            col = 0 if i == 0 else len(commands[i - 1]) + 4
            self.screen.addstr(y - 2, col, commands[i])

        # initialize threads and synchronization items
        self.threads.append(threading.Thread(target=self._process_input,
                                             daemon=True))
        self.threads.append(threading.Thread(target=self._calculate_cpu,
                                             daemon=True))
        self.threads.append(threading.Thread(target=self._load_commands,
                                             daemon=True))
        self.threads.append(threading.Thread(target=self._display_to_screen,
                                             daemon=True))
        for thread in self.threads:
            thread.start()

        self.exit_event.wait()
        self._exit_mode()

        return self.exit_event.get_value()

    def get_next_mode(self):

        """
        :return: the next mode to be run after this object
        """

        return self.exit_event.get_value()

    @staticmethod
    def initialize_vim(working_path, pipe_name):
        # file initializations relative to working paths
        plugin_file = os.path.join(working_path, 'plugin.vim')

        # lay em with the pipe
        os.mkfifo(pipe_name)

        # create the vim command that opens up vim instance in new terminal
        # with proper settings, etc.
        vim_command = ('vim -S %r -c %r' % (plugin_file, 'call AutoLogInfo()'))

        # send command to open up new process, wait for command process to die
        # before getting the pid of the actual vim process (this is like a
        # super jank way of doing it but oh well (no i'm not closing these
        # parentheses
        args = [env_command[desktop_env], '-e', vim_command]
        proc = subprocess.Popen(args).pid
        os.waitid(os.P_PID, int(proc), os.WEXITED)
        while True:
            try:
                logging.debug(vim_command)
                proc = (subprocess.Popen(['pgrep', '-f', vim_command[:7]],
                                         stdout=subprocess.PIPE)
                                  .stdout.read().decode('utf-8').rstrip())
                logging.debug(proc)
                proc = int(proc)
                break
            except:
                pass
        return proc
