import os
import time
import collections
import json
import sqlite3
import curses


HERTZ = 250
try:
    os.remove('commands.db')
except OSError:
    pass


def process_input(input_queue, screen, exit_event):
    while not exit_event.is_set():
        try:
            keypress = screen.getkey()
            input_queue.put(keypress)
        except curses.error:
            pass


def calculate_cpu(interval, display_queue, exit_event):
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
    while not exit_event.is_set():
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
        display_queue.put(cpu_usage)

        time.sleep(interval)

        utime_prev = utime_next
        stime_prev = stime_next
        cutime_prev = cutime_next
        cstime_prev = cstime_next
        time_prev = time_next


def display_commands(display_queue, screen, exit_event):
    y, x = screen.getmaxyx()
    display_deque = collections.deque(maxlen=y-2)
    while not exit_event.is_set():
        if not display_queue.empty():
            display_deque.append(display_queue.get())
            curses.setsyx(0, 0)
            for i, item in enumerate(display_deque):
                screen.clrtoeol()
                screen.addstr(i, 0, str(item)[:x-2])
                screen.noutrefresh()
            curses.doupdate()


def load_commands(pipe_name, display_queue, exit_event):
    conn = sqlite3.connect('commands.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE commands
                 (time, command)''')
    with open(pipe_name, 'r') as pipe:
        while not exit_event.is_set():
            line = pipe.readline()
            if line.rstrip() == '':
                continue
            command = json.loads(line, encoding='utf-8')

            display_queue.put(command)
    conn.commit()
    conn.close()
