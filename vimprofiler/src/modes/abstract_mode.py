import abc
import logging

logging.basicConfig(filename='logging_stuff.log', level=logging.DEBUG)


class Mode(object):

    """ Abstract base class for different modes
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, screen, working_path, screen_lock):

        """
        constructor for any mode
        :param screen: curses screen that this mode is operating on
        :param working_path: working path of original main.py
        :param screen_lock: a lock that controls access to the screen, should be used any time cursor might be used
        :return:
        """

        self.screen = screen
        self.working_path = working_path
        self.screen_lock = screen_lock

    @abc.abstractmethod
    def run(self):
        pass

    def _get_stream_input(self, command):
        with self.screen_lock:
            self.screen.nodelay(0)  # make IO blocking for now
            y, x = self.screen.getmaxyx()
            stream = ''
            self.screen.addstr(y-1, 0, command + ':')
            self.screen.refresh()
        while True:
            keypress = self.screen.getkey()
            if keypress == '\n':  # capture enter key
                with self.screen_lock:
                    self.screen.move(y-1, 0)
                    self.screen.clrtoeol()
                    self.screen.refresh()
                    logging.debug('stream: ' + repr(stream))
                    return stream
            else:  # contains any modification to input
                if keypress == '\x7f':  # capture backspace key
                    if len(stream) > 0:
                        stream = stream[:-1]
                else:
                    stream += keypress
                with self.screen_lock:
                    self.screen.move(y-1, 0)
                    self.screen.clrtoeol()
                    self.screen.addstr(y-1, 0, command + ':' + stream)
                    self.screen.refresh()
