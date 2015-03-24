import subprocess
import os
import threading
import time


def print_hello_world():
    time.sleep(5)
    print('hello world')


if __name__=='__main__':
    startup_file = 'vimprofile-startuptime.log'

    os.remove(startup_file)
    vim_command = 'vim --startuptime vimprofile-startuptime.log -S plugin.vim'
    args = ['gnome-terminal', '-e', vim_command]


    proc = subprocess.Popen(args).pid

    os.waitid(os.P_PID, int(proc), os.WEXITED)

    proc = int(subprocess.Popen(['pgrep', '-f', vim_command],
                                stdout=subprocess.PIPE).stdout.read().decode('utf-8').rstrip())

    # sample threading before blocking for waiting on vim
    t = threading.Thread(target=print_hello_world, daemon=True)
    t.start()

    while True:
        try:
            os.kill(proc, 0)
        except OSError:
            break

