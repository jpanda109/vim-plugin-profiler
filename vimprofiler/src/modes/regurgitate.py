import os
import logging
import tempfile
import threading
import queue
import subprocess
import time
import collections
import json
import sqlite3
import curses

from ..lib import utils


logging.basicConfig(filename='logging_stuff.log', level=logging.DEBUG)
HERTZ = 250  # Clock Hertz of computer (shouldn't hard code but whatev)
env_command = {
    'ubuntu': 'gnome-terminal',
    'xubuntu': 'xfce4-terminal'
}
desktop_env = os.environ.get('DESKTOP_SESSION')


""" tasks to be run by threads"""


def _calculate_cpu(interval, display_queue, exit_event):

    """ calculate_cpu and send to display_queue """

    proc_file_name = '/proc/' + str(os.getpid()) + '/stat'
    time_file_name = '/proc/stat'
    utime_prev = 0
    utime_next = 0
    stime_prev = 0
    stime_next = 0
    cutime_prev = 0
    cutime_next = 0
    cstime_prev = 0
    cstime_next = 0
    time_prev = 0
    time_next = 0
    with open(time_file_name, 'r') as time_file:
        time_stats = time_file.readline().split(' ')[2:]
    time_prev = sum(map(float, time_stats))
    time.sleep(interval)
    while not exit_event.is_set():
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
        display_queue.put(cpu_usage)

        time.sleep(interval)

        utime_prev = utime_next
        stime_prev = stime_next
        cutime_prev = cutime_next
        cstime_prev = cstime_next
        time_prev = time_next


def _display_to_screen(display_queue, screen, exit_event):

    """ display stuff to curses """

    y, x = screen.getmaxyx()
    display_deque = collections.deque(maxlen=y-4)
    while not exit_event.is_set():
        if not display_queue.empty():
            display_deque.append(display_queue.get())
            curses.setsyx(0, 0)
            for i, item in enumerate(display_deque):
                screen.clrtoeol()
                screen.addstr(i, 0, str(item)[:x-2])
                screen.noutrefresh()
            curses.doupdate()


def _load_commands(pipe_name, display_queue, exit_event):

    """ receive the commands sent through pipe from the vim process """

    try:
        os.remove('commands.db')
    except OSError:
        pass
    conn = sqlite3.connect('commands.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE commands
                 (time, command)''')
    with open(pipe_name, 'r') as pipe:
        while not exit_event.is_set():
            line = pipe.readline()
            if line.rstrip() == '':
                continue
            command = json.loads(line, encoding='utf-8')
            display_queue.put(command)
            c.execute('INSERT INTO commands VALUES (?,?)',
                      (command['time'], command['command']))
    conn.commit()
    conn.close()


def _process_input(screen, exit_event):

    """ put keypresses into input queue """

    while not exit_event.is_set():
        try:
            keypress = screen.getkey()
            logging.debug(keypress)
            if keypress == 'q' or keypress == 'Q':
                exit_event.set(0)
            if keypress == '1':
                exit_event.set(1)
        except curses.error:
            pass


""" non-threaded program logic """


def _exit_mode(threads, proc, screen):

    """ gracefully clean up everything this mode was doing """

    for thread in threads:
        screen.clear()
        screen.addstr(0, 0, 'cleaning up')
        screen.refresh()
        thread.join()
    try:
        os.kill(proc, 9)
    except OSError:
        pass


def main(screen, working_path):

    """ main function for this mode
    :param screen: screen that this mode is operating on
    :working_path: working path for things like plugin.vim
    """

    y, x = screen.getmaxyx()

    # display mode specific commands on line y - 2
    commands = ['a: Analyze', 'o: Open']
    for i in range(len(commands)):
        col = 0 if i == 0 else len(commands[i - 1]) + 4
        screen.addstr(y - 2, col, commands[i])

    # file initializations relative to working paths
    plugin_file = os.path.join(working_path, 'plugin.vim')

    with tempfile.TemporaryDirectory() as tmpdir:
        # lay em with the pipe
        pipe_name = os.path.join(tmpdir, 'tmpfifo')
        os.mkfifo(pipe_name)
        os.environ['VIMUALIZER_PIPE_NAME'] = pipe_name

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

        # initialize threads and synchronization items
        threads = []
        exit_event = utils.ValueEvent()
        display_queue = queue.Queue()
        threads.append(threading.Thread(target=_process_input,
                                        args=(screen, exit_event),
                                        daemon=True))
        threads.append(threading.Thread(target=_calculate_cpu,
                                        args=(1, display_queue, exit_event),
                                        daemon=True))
        threads.append(threading.Thread(target=_load_commands,
                                        args=(pipe_name, display_queue,
                                              exit_event),
                                        daemon=True))
        threads.append(threading.Thread(target=_display_to_screen,
                                        args=(display_queue, screen,
                                              exit_event),
                                        daemon=True))
        for thread in threads:
            thread.start()

        exit_event.wait()
        _exit_mode(threads, proc, screen)
    return exit_event.get_value()
