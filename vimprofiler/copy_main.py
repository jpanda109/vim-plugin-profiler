import subprocess
import os
import sys
import tempfile
import threading
import queue
import argparse
import src.tasks as tasks


def parse_args():
    parser = argparse.ArgumentParser(description='Run vim in a sandbox')
    parser.add_argument('files', metavar='F', type=str, nargs='*',
                        help='files to be edited with vim')
    return parser.parse_args()


if __name__ == '__main__':

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

        # create the vim command to be sent to seperate terminal
        vim_command = ('vim --startuptime %r -S %r -c %r' %
                       (startup_file, plugin_file, 'call AutoLogInfo()'))
        files_string = ' '
        for f in args.files:
            files_string += f
        vim_command += files_string

        # open new process, wait for command process to die before getting pid
        # of the vim process itself (using pgrep ayy)
        args = ['gnome-terminal', '-e', vim_command]
        proc = subprocess.Popen(args).pid
        os.waitid(os.P_PID, int(proc), os.WEXITED)
        proc = int(subprocess.Popen(['pgrep', '-f', vim_command[:10]],
                                    stdout=subprocess.PIPE)
                   .stdout.read().decode('utf-8').rstrip())

        # start threads
        input_queue = queue.Queue()
        input_thread = threading.Thread(target=tasks.process_input,
                                        args=(input_queue,), daemon=True)
        input_thread.start()

        # main loop, process info etc
        with open(pipe_name, 'r') as pipe:
            while True:

                # deal with user input
                if not input_queue.empty():
                    keypress = input_queue.get()
                    if keypress == 'Q':
                        os.kill(proc, 9)
                        sys.exit()
                    elif keypress == 'q':
                        os.kill(proc, 9)

                # deal with info received through pipe
                line = pipe.readline()
                if line.rstrip() != '':
                    print(line)
                try:
                    os.kill(proc, 0)
                except OSError:
                    break
