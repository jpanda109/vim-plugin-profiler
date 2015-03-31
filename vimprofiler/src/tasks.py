import os
import time
import collections


HERTZ = 250


def process_input(input_queue, screen):
    while True:
        keypress = screen.getkey()
        input_queue.put(keypress)


def calculate_cpu(interval, screen, lock):
    y, x = screen.getmaxyx()
    cpu_queue = collections.deque(maxlen=y-2)
    proc_file_name = '/proc/' + str(os.getpid()) + '/stat'
    time_file_name = '/proc/stat'
    utime_prev = 0
    utime_next = 0
    stime_prev = 0
    stime_next = 0
    cutime_prev = 0
    cutime_next = 0
    cstime_prev = 0
    cstime_next = 0
    time_prev = 0
    time_next = 0
    with open(time_file_name, 'r') as time_file:
        time_stats = time_file.readline().split(' ')[2:]
    time_prev = sum(map(float, time_stats))
    time.sleep(interval)
    while True:
        with open(proc_file_name, 'r') as proc_file:
            stats = proc_file.readline().split(' ')
        with open(time_file_name, 'r') as time_file:
            time_stats = time_file.readline().split(' ')[2:]
        utime_next = float(stats[13])
        stime_next = float(stats[14])
        cutime_next = float(stats[15])
        cstime_next = float(stats[16])

        time_next = sum(map(float, time_stats))
        seconds = time_next - time_prev

        total_time = (utime_next - utime_prev) + (stime_next - stime_prev)
        total_time += (cutime_next - cutime_prev) + (cstime_next - cstime_prev)
        cpu_usage = 100 * ((total_time / HERTZ) / seconds)
        cpu_queue.append(cpu_usage)
        # cpu_queue.put((cpu_usage, time.time()))

        with lock:
            for i, cpu in enumerate(cpu_queue):
                screen.addstr(i, 70, str(cpu))
                screen.refresh()

        time.sleep(interval)

        utime_prev = utime_next
        stime_prev = stime_next
        cutime_prev = cutime_next
        cstime_prev = cstime_next
        time_prev = time_next
