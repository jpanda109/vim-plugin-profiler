import abc


class Mode(object):

    """ Abstract base class for different modes
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def run(self):
        pass

    @abc.abstractmethod
    def get_next_mode(self):
        pass