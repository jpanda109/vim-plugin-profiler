import subprocess
import os

startup_file = 'vimprofile-startuptime.log'

os.remove(startup_file)
vim_command = 'vim --startuptime vimprofile-startuptime.log -S plugin.vim'
args = ['gnome-terminal', '-e', vim_command]


proc = subprocess.Popen(args).pid

os.waitid(os.P_PID, int(proc), os.WEXITED)

proc = int(subprocess.Popen(['pgrep', '-f', vim_command],
                        stdout=subprocess.PIPE).stdout.read().decode('utf-8').rstrip())
print(proc)
while True:
    try:
        os.kill(proc, 0)
    except OSError:
        break

