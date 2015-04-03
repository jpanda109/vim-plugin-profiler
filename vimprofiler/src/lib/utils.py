import threading


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
