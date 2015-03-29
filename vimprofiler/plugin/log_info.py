import vim
import os

command = vim.eval('a:command')
pipename = os.environ['VIMUALIZER_PIPE_NAME']
with open(pipename, 'w') as pipe:
    pipe.write(command.encode('utf-8'))
