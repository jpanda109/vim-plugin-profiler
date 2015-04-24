import vim
import time
import json

#Takes in command & start time from vim and passes it into the pipe

command = vim.eval('a:command')
start_time = vim.eval('a:start_time')

with open('tmpfifo', 'w') as pipe:
    data = {
        'time': time.time() - float(start_time),
        'command': command,
    }
    data_string = json.dumps(data, pipe) + '\n'
    pipe.write(data_string)
