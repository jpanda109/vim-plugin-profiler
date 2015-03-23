import os

pipe_name = ''
with open('pipe_name', 'r') as pnfile:
    pipe_name = pnfile.readline()

with open(pipe_name, 'r') as pipe:
    print(pipe.read())


os.remove('pipe_name')
