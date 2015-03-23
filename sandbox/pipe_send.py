import tempfile
import os
import time

with tempfile.TemporaryDirectory() as tmpdir:
    filename = os.path.join(tmpdir, 'tmpfifo')
    with open('pipe_name', 'w') as pnfile:
        pnfile.write(filename)

    try:
        os.mkfifo(filename)
    except OSError as e:
        print(e)

    print(filename)
    fifo = os.open(filename, os.O_WRONLY)
    print('opened')
    for i in range(5):
        os.write(fifo, (str(i) + '\n').encode('utf-8'))
        time.sleep(1)
    os.close(fifo)
