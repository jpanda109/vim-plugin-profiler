import os
import time


HERTZ = 250


def process_input(input_queue, screen):
    while True:
        keypress = screen.getkey()
        input_queue.put(keypress)


def calculate_cpu(cpu_queue, interval):
    proc_file_name = '/proc/' + str(os.getpid()) + '/stat'
    stat_file_name = '/proc/uptime'
    utime_prev = 0
    utime_next = 0
    stime_prev = 0
    stime_next = 0
    cutime_prev = 0
    cutime_next = 0
    cstime_prev = 0
    cstime_next = 0
    while True:
        with open(proc_file_name, 'r') as proc_file:
            stats = proc_file.readline().split(' ')
        with open(stat_file_name, 'r') as stat_file:
            uptime_stats = stat_file.readline().split(' ')
        utime_next = float(stats[13])
        stime_next = float(stats[14])
        cutime_next = float(stats[15])
        cstime_next = float(stats[16])
        start_time = float(stats[21])
        uptime = float(uptime_stats[0])

        seconds = uptime - (start_time / HERTZ)

        total_time = (utime_next - utime_prev) + (stime_next - stime_prev)
        total_time += (cutime_next - cutime_prev) + (cstime_next - cstime_prev)
        cpu_usage = 100 * ((total_time / HERTZ) / seconds)
        cpu_queue.put((cpu_usage, time.time()))

        time.sleep(interval)

        utime_prev = utime_next
        stime_prev = stime_next
        cutime_prev = cutime_next
        cstime_prev = cstime_next
