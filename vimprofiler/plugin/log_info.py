import vim
import os
import time
import json

command = vim.eval('a:command')
pipename = os.environ['VIMUALIZER_PIPE_NAME']
with open(pipename, 'w') as pipe:
    data = {
        'time': time.time(),
        'command': command,
        'pid': os.getpid()
    }
    data_string = json.dump(data, pipe)
    # pipe.write(data_string)
    # pipe.write(command.encode('utf-8'))
