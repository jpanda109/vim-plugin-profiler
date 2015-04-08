import threading
import os


class ValueEvent():

    """ container for multiple threading.Event(s) """

    def __init__(self, value=None):
        self.event = threading.Event()
        self.value = value

    def is_set(self):
        return self.event.is_set()

    def set(self, value):
        self.value = value
        self.event.set()

    def clear(self, value=None):
        if value is not None:
            self.value = value
        self.event.clear()

    def wait(self, timeout=None):
        self.event.wait(timeout=timeout)

    def get_value(self):
        return self.value


def remove_file(path):
    try:
        os.remove(path)
    except OSError:
        pass


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
