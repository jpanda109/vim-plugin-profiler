import sys


def process_input(input_queue):
    while True:
        user_input = sys.stdin.read(1)
        input_queue.put(user_input)
