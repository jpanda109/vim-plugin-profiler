# STL imports
import argparse
import os
import logging
import tempfile
import threading
import queue
import subprocess

# user-defined imports
import src.wrappers as wrappers
import src.tasks as tasks


logging.basicConfig(filename='logging_stuff.log', level=logging.DEBUG)


def parse_args():
    """ parse command line arguments """
    parser = argparse.ArgumentParser(description='Run vim in a sandbox')
    parser.add_argument('files', metavar='F', type=str, nargs='*',
                        help='files to be edited with vim')
    return parser.parse_args()


@wrappers.safe_exc
def main(screen, working_path):
    """ main curses screen logic; I think everything before with open(pipe_name)
    can actuall be moved elsewhere for code prettyness"""
    args = parse_args()

    # file initializations relative to working paths
    # working_path = os.path.dirname(os.path.abspath(__file__))
    # working_path = os.environ['cur_working_path']
    startup_file = os.path.join(working_path, 'vimprofile-startuptime.log')
    plugin_file = os.path.join(working_path, 'plugin.vim')

    try:
        os.remove(startup_file)
    except FileNotFoundError:
        pass

    with tempfile.TemporaryDirectory() as tmpdir:
        # lay em with the pipe
        pipe_name = os.path.join(tmpdir, 'tmpfifo')
        os.mkfifo(pipe_name)
        os.environ['VIMUALIZER_PIPE_NAME'] = pipe_name

        # create the vim command that opens up vim instance in new terminal
        # with proper settings, etc.
        vim_command = ('vim --startuptime %r -S %r -c %r' %
                       (startup_file, plugin_file, 'call AutoLogInfo()'))
        files_string = ' '
        for f in args.files:
            files_string += f
        vim_command += files_string

        # send command to open up new process, wait for command process to die
        # before getting the pid of the actual vim process (this is like a
        # super jank way of doing it but oh well (no i'm not closing these
        # parentheses
        args = ['gnome-terminal', '-e', vim_command]
        proc = subprocess.Popen(args).pid
        os.waitid(os.P_PID, int(proc), os.WEXITED)
        proc = int(subprocess.Popen(['pgrep', '-f', vim_command[:10]],
                                    stdout=subprocess.PIPE)
                   .stdout.read().decode('utf-8').rstrip())

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
                """
                if keypress == 'q' or keypress == 'Q':
                    exit_event.set()
                    for thread in threads:
                        thread.join()
                    os.kill(proc, 9)
                    break
                """
        exit_program(threads, proc)


def exit_program(threads, proc):
    for thread in threads:
        logging.debug('thread')
        thread.join()
    try:
        os.kill(proc, 9)
    except OSError:
        pass


def handle_input(keypress, exit_event):
    if keypress == 'q' or keypress == 'Q':
        exit_event.set()
