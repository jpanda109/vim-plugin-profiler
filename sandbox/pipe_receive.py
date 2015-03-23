import os

pipe_name = ''
with open('pipe_name', 'r') as pnfile:
    pipe_name = pnfile.readline()

with open(pipe_name, 'r') as pipe:
    while True:  # os.path.isfile(pipe_name):
        print(pipe.readline()[:-1])
        if not os.path.exists(pipe_name):
            print('doesnt exist')
            break


os.remove('pipe_name')
