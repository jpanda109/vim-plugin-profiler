import subprocess
import os
import sys
import tempfile
import src.tasks as tasks
import threading
import queue


if __name__ == '__main__':

    # file initializations relative to working paths
    working_path = os.path.dirname(os.path.abspath(__file__))
    startup_file = os.path.join(working_path, 'vimprofile-startuptime.log')
    plugin_file = os.path.join(working_path, 'plugin.vim')

    try:
        os.remove(startup_file)
    except FileNotFoundError:
        pass

    with tempfile.TemporaryDirectory() as tmpdir:
        pipe_name = os.path.join(tmpdir, 'tmpfifo')
        try:
            os.mkfifo(pipe_name)
        except OSError as e:
            print(e)
        os.environ['VIMUALIZER_PIPE_NAME'] = pipe_name
        vim_command = 'vim --startuptime %r -S %r' % (startup_file,
                                                      plugin_file)
        args = ['gnome-terminal', '-e', vim_command]

        proc = subprocess.Popen(args).pid
        os.waitid(os.P_PID, int(proc), os.WEXITED)

        try:
            proc = int(subprocess.Popen(['pgrep', '-f', vim_command[:10]],
                                        stdout=subprocess.PIPE)
                       .stdout.read().decode('utf-8').rstrip())
            print(proc)
        except ValueError:
            proc = 0

        # start threads
        input_queue = queue.Queue()
        input_thread = threading.Thread(target=tasks.process_input,
                                        args=(input_queue,), daemon=True)
        input_thread.start()
        with open(pipe_name, 'r') as pipe:
            while True:
                line = pipe.readline()
                if line.rstrip() != '':
                    print(line)
                if not input_queue.empty():
                    if (input_queue.get() == 'q'):
                        os.kill(proc, 9)
                        sys.exit()
                try:
                    os.kill(proc, 0)
                except OSError:
                    break
