import vim
import os
import time
import json

command = vim.eval('a:command')
pipename = os.environ['VIMUALIZER_PIPE_NAME']
with open(pipename, 'w') as pipe:
    proc_file_name = '/proc/' + str(os.getpid()) + '/stat'
    with open(proc_file_name, 'r') as proc_file:
        stats = proc_file.readline().split(' ')
        utime = stats[13]
        stime = stats[14]
        cutime = stats[15]
        cstime = stats[15]

    data = {
        'time': time.time(),
        'command': command,
        'utime': utime,
        'stime': stime,
        'cutime': cutime,
        'cstime': cstime
    }
    data_string = json.dump(data, pipe)
    # pipe.write(data_string)
    # pipe.write(command.encode('utf-8'))
