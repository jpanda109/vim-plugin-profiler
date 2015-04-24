import functools
import traceback

#Wrappers for our own use within this app

def safe_exc(f):

    """wraps a function such that it now returns a traceback of any exceptions
    throw"""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            return traceback.format_exc()
    return wrapper
