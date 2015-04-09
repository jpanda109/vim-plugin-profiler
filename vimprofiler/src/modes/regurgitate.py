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

    def __init__(self, screen, working_path, screen_lock):

        """
        Initializes this mode
        :param screen: screen that you're working with
        :param working_path: path where things like plugin.vim is stored
        :return:
        """
        super().__init__(screen=screen, working_path=working_path, screen_lock=screen_lock)
        self.exit_event = utils.ValueEvent()  # event signaling when threads should end
        self.vim_quit_event = threading.Event()  # event signaling when the vim process is done
        self.interval = 1  # interval of cpu calculations
        self.display_queue = queue.Queue()  # atomic queue for displaying info
        self.pipe_name = os.path.join(self.working_path, 'tmpfifo')  # pathname named pipe
        self.proc = self.initialize_vim(self.working_path, self.pipe_name)  # pid of vim process
        self.threads = []  # list of threads

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
        while not self.exit_event.is_set() and not self.vim_quit_event.is_set():

            # get all the needed info
            with open(proc_file_name, 'r') as proc_file:
                stats = proc_file.readline().split(' ')
            with open(time_file_name, 'r') as time_file:
                time_stats = time_file.readline().split(' ')[2:]
            utime_next = float(stats[13])
            stime_next = float(stats[14])
            cutime_next = float(stats[15])
            cstime_next = float(stats[16])

            # calcurations
            time_next = sum(map(float, time_stats))
            seconds = time_next - time_prev

            total_time = (utime_next - utime_prev) + (stime_next - stime_prev)
            total_time += (cutime_next - cutime_prev) + (cstime_next - cstime_prev)
            cpu_usage = 100 * ((total_time / HERTZ) / seconds)

            # place into display queue so another thread can handle
            self.display_queue.put('{:.2%}'.format(cpu_usage))
            time.sleep(self.interval)

            # get ready for next  iteration
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

    def _check_status(self):

        """
        checks whether or not the vim process is still alive
        :return:
        """

        while not self.exit_event.is_set():
            try:
                os.kill(self.proc, 0)
            except OSError:
                self.vim_quit_event.set()

    def _analyze_profile(self):

        """
        analyzes top 10 or so function calls, sorted by total time spent on each function call
        :return:
        """

        if not self.vim_quit_event.is_set():
            return

        profile_path = os.path.join(self.working_path, 'profile.log')
        with open(profile_path) as profile:
            lines = []
            begin = False
            for line in profile:
                if line.rstrip() == 'FUNCTIONS SORTED ON TOTAL TIME':
                    begin = True
                    continue
                if begin:
                    if line.rstrip() == '':
                        begin = False
                    else:
                        lines.append(line.rstrip())
        for l in lines:
            self.display_queue.put(l)

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
                if keypress == 'a':
                    self._analyze_profile()
                if keypress == 'i':
                    stream = self._get_stream_input(keypress)
                    logging.debug('stream: ' + stream)
                    if utils.is_float(stream):
                        self.interval = float(stream)
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
        utils.remove_file(self.pipe_name)
        swap_file_path = os.path.join(self.working_path, '.swp')
        utils.remove_file(swap_file_path)
        profile_path = os.path.join(self.working_path, 'profile.log')
        utils.remove_file(profile_path)

    def run(self):

        """ main function for this mode
        :return the mode that should be switched to
        """

        # display mode specific commands on line y - 2
        y, x = self.screen.getmaxyx()
        commands = ['a: Analyze', 'o: Open', 'i: interval']
        prev_col = 0
        for i in range(len(commands)):
            col = 0 if i == 0 else len(commands[i - 1]) + 4
            col += prev_col
            self.screen.addstr(y - 3, col, commands[i])
            prev_col = col

        # initialize threads and synchronization items
        self.threads.append(threading.Thread(target=self._process_input,
                                             daemon=True))
        self.threads.append(threading.Thread(target=self._calculate_cpu,
                                             daemon=True))
        self.threads.append(threading.Thread(target=self._load_commands,
                                             daemon=True))
        self.threads.append(threading.Thread(target=self._display_to_screen,
                                             daemon=True))
        self.threads.append(threading.Thread(target=self._check_status,
                                             daemon=True))
        for thread in self.threads:
            thread.start()

        self.exit_event.wait()
        self._exit_mode()

        return self.exit_event.get_value()

    @staticmethod
    def initialize_vim(working_path, pipe_name):

        """
        Initialize the vim process along with creating a named pipe to communicate with it
        :param working_path: working path of main.py and other files
        :param pipe_name: pathname of pipe to be created
        :return: pid of vim process
        """

        # file initializations relative to working paths
        plugin_file = os.path.join(working_path, 'plugin.vim')

        # lay em with the pipe
        utils.remove_file(pipe_name)
        os.mkfifo(pipe_name)

        # create the vim command that opens up vim instance in new terminal
        # with proper settings, etc.
        profile_path = os.path.join(working_path, 'profile.log')
        startup_command = 'call AutoLogInfo() | profile start ' + profile_path + ' | profile func * | profile file *'
        vim_command = ('vim -S %r -c %r' % (plugin_file, startup_command))

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
