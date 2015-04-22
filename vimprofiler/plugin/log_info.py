import vim
import time
import json

command = vim.eval('a:command')
start_time = vim.eval('a:start_time')

with open('tmpfifo', 'w') as pipe:
    data = {
        'time': time.time() - float(start_time),
        'command': command,
    }
    data_string = json.dumps(data, pipe) + '\n'
    pipe.write(data_string)
