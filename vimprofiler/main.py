import subprocess
import os
import threading
import time


def print_hello_world():
    time.sleep(5)
    print('hello world')


if __name__ == '__main__':
    working_path = os.path.dirname(os.path.abspath(__file__))
    # file initializations
    startup_file = os.path.join(working_path, 'vimprofile-startuptime.log')
    plugin_file = os.path.join(working_path, 'plugin.vim')
    print(working_path)

    try:
        os.remove(startup_file)
    except FileNotFoundError:
        pass
    vim_command = 'vim --startuptime %r -S %r' % (startup_file, plugin_file)
    args = ['gnome-terminal', '-e', vim_command]

    proc = subprocess.Popen(args).pid

    os.waitid(os.P_PID, int(proc), os.WEXITED)

    try:
        proc = int(subprocess.Popen(['pgrep', '-f', vim_command[:10]],
                                stdout=subprocess.PIPE).stdout.read().decode('utf-8').rstrip())
        print(proc)
    except ValueError:
        proc = 0

    # sample threading before blocking for waiting on vim
    t = threading.Thread(target=print_hello_world, daemon=True)
    t.start()

    while True:
        try:
            os.kill(proc, 0)
        except OSError:
            break

