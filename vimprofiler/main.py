import curses
import sys
import subprocess
import os
import tempfile
import argparse
import threading
import queue
import src.wrappers as wrappers
import src.tasks as tasks


def parse_args():
    """ parse command line arguments """
    parser = argparse.ArgumentParser(description='Run vim in a sandbox')
    parser.add_argument('files', metavar='F', type=str, nargs='*',
                        help='files to be edited with vim')
    return parser.parse_args()


@wrappers.safe_exc
def main(screen):
    """ main curses screen logic; I think everything before with open(pipe_name)
    can actuall be moved elsewhere for code prettyness"""
    args = parse_args()

    # file initializations relative to working paths
    working_path = os.path.dirname(os.path.abspath(__file__))
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

        # initialize threads and locks, etc
        threads = []
        exit_event = threading.Event()
        screen_lock = threading.Lock()
        input_queue = queue.Queue()
        threads.append(threading.Thread(target=tasks.process_input,
                                        args=(input_queue, screen, exit_event),
                                        daemon=True))
        threads.append(threading.Thread(target=tasks.calculate_cpu,
                                        args=(1, screen, screen_lock,
                                              exit_event),
                                        daemon=True))
        threads.append(threading.Thread(target=tasks.display_commands,
                                        args=(pipe_name, screen, screen_lock,
                                              exit_event),
                                        daemon=True))
        for thread in threads:
            thread.start()

        # main program logic and curses manipulation starts here
        while True:
            if not input_queue.empty():
                keypress = input_queue.get()
                if keypress == 'q' or keypress == 'Q':
                    exit_event.set()
                    for thread in threads:
                        thread.join()
                    os.kill(proc, 9)
                    sys.exit()
            try:
                os.kill(proc, 0)
            except OSError:
                break


if __name__ == "__main__":
    myscreen = curses.initscr()
    curses.noecho()
    myscreen.nodelay(1)

    exc = main(myscreen)

    curses.echo()
    curses.endwin()

    if exc is not None:
        print(exc)
