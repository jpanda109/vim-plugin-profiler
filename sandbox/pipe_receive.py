import os
import tempfile
import queue
import threading
import sys
import curses


def process_input(input_queue):
    while True:
        input_queue.put(sys.stdin.read(1))


with tempfile.TemporaryDirectory() as tmpdir:
    # create readable filename with pipe info in it for other processes to use
    filename = os.path.join(tmpdir, 'tmpfifo')
    with open('pipe_name', 'w') as pnfile:
        pnfile.write(filename)

    # create a thread that listens to input
    input_queue = queue.Queue()
    input_thread = threading.Thread(target=process_input, args=(input_queue,),
                                    daemon=True)
    input_thread.start()

    try:
        os.mkfifo(filename)
    except OSError as e:
        print(e)

    pipe_name = ''
    with open('pipe_name', 'r') as pnfile:
        pipe_name = pnfile.readline()

    with open(pipe_name, 'r') as pipe:
        print("Time" + " Command")
        while True:
            if not input_queue.empty():
                if (input_queue.get() == 'q'):
                    break
            line = pipe.readline()[:-1]
            if line.rstrip() != '':
                my_list = line.split(' ', 1);
                print('{:>12} {:>12 }'.format(my_list[1],my_list[2])

    os.remove('pipe_name')
