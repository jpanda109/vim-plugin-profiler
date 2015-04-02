import threading


class MultiEvent():

    """ container for multiple threading.Event(s) """

    def __init__(self, *events):
        self.events = {}
        for event in events:
            self.events[event] = threading.Event()

    def is_set(self, *events):
        rv = []
        for e in events:
            rv.append(e.is_set())
        return rv

    def set(self, *events):
        for e in events:
            e.set()

    def clear(self, *events):
        for e in events:
            e.clear()

    def wait(self, *events, timeout=None):
        for e in events:
            e.wait(timeout=timeout)
