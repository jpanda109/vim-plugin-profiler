import os
import time


def write_to_pipe(pipe, text):
    os.write(pipe, text.encode('utf-8'))


pipe_name = ''
with open('pipe_name', 'r') as pnfile:
    pipe_name = pnfile.readline()


pipe = os.open(pipe_name, os.O_WRONLY)
for i in range(5):
    os.write(pipe, (str(i) + '\n').encode('utf-8'))
    time.sleep(1)
