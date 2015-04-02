import vim
import time
import json

command = vim.eval('a:command')
with open('tmpfifo', 'w') as pipe:
    data = {
        'time': time.time(),
        'command': command,
    }
    data_string = json.dumps(data, pipe) + '\n'
    pipe.write(data_string)
