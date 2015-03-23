import os

pipe_name = ''
with open('pipe_name', 'r') as pnfile:
    pipe_name = pnfile.readline()

with open(pipe_name, 'r') as pipe:
    for i in range(5):
        print(pipe.readline()[:-1])


os.remove('pipe_name')
