import vim
import time
import json

command = vim.eval('a:command')
start_time = vim.eval('a:start_time')

#def myfunc():
#    myfunc.my_var = False
#    myfunc.starttime = None

#if not myfunc.my_var:
#    myfunc.my_var = True
#    myfunc.starttime = time.time()

#start_time = time.time()


with open('tmpfifo', 'w') as pipe:
    data = {
        'time': time.time() - float(start_time),
        'command': command,
    }
    data_string = json.dumps(data, pipe) + '\n'
    pipe.write(data_string)


#matt's note:
#argh im trying to get a starttime so that time is relative instead of
#absolute (ie. start at 0 and go from there), but i dont know jack about python and so something simple
#is really annoying cause i dont know scope.
#sigh.
