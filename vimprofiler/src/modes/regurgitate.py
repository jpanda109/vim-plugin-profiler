import os
import logging
import tempfile
import threading
import queue
import subprocess

from ..lib import tasks

logging.basicConfig(filesname='logging_stuff.log', level=logging.DEBUG)


def exit_mode(threads, proc, screen):
    for thread in threads:
        screen.clear()
        screen.addstr(0, 0, 'cleaning up')
        screen.refresh()
        logging.debug('thread')
        thread.join()
    try:
        os.kill(proc, 9)
    except OSError:
        pass


def handle_input(keypress, exit_event):
    if keypress == 'q' or keypress == 'Q':
        exit_event.set()


def main(screen, working_path):
    """ main function for this mode """

    y, x = screen.getmaxyx()
    screen.clear()
    screen.addstr(y - 1, 0, 'q: QUIT')

    # file initializations relative to working paths
    # working_path = os.path.dirname(os.path.abspath(__file__))
    # working_path = os.environ['cur_working_path']
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
        args = ['gnome-terminal', '-e', vim_command]
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
        exit_event = threading.Event()
        display_queue = queue.Queue()
        input_queue = queue.Queue()
        threads.append(threading.Thread(target=tasks.process_input,
                                        args=(input_queue, screen, exit_event),
                                        daemon=True))
        threads.append(threading.Thread(target=tasks.calculate_cpu,
                                        args=(1, display_queue, exit_event),
                                        daemon=True))
        threads.append(threading.Thread(target=tasks.load_commands,
                                        args=(pipe_name, display_queue,
                                              exit_event),
                                        daemon=True))
        threads.append(threading.Thread(target=tasks.display_commands,
                                        args=(display_queue, screen,
                                              exit_event),
                                        daemon=True))
        for thread in threads:
            thread.start()

        # main program logic and curses manipulation starts here
        while not exit_event.is_set():
            if not input_queue.empty():
                logging.debug('check_input_queue')
                keypress = input_queue.get()
                handle_input(keypress, exit_event)
        exit_mode(threads, proc, screen)
