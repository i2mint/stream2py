"""
FlaskRequest Source
"""

__all__ = ['FlaskRequestReader']

from stream2py import SourceReader


class FlaskRequestReader(SourceReader):
    """A source reader that reads from an incoming HTTP request using Flask.
    Must be instantiated from a Flask request handler function to ensure
    that the flask.request context is available.
    """

    _request = None
    _chk_size = 2048

    def __init__(self, chk_size=2048):
        """
        :param chk_size: Specifies the chunk size to read (default 2048 bytes)
        """
        self._chk_size = chk_size
        pass

    @property
    def info(self) -> dict:
        """
        Returns the __init__ arguments for the instance.

        :return: dict
        """
        _info = {'chk_size': self._chk_size}
        return _info

    def key(self, data):
        return data

    def open(self):
        try:
            from flask import request

            self._request = request
            self._stream = request.stream
        except:
            raise ModuleNotFoundError(
                'FlaskRequestReader requires flask to be installed'
            )

    def close(self):
        self._request = None
        self._stream = None

    def read(self):
        """Reads raw bytes if the request body is not finished yet.
        Raises a StopIteration exception if the request has finished.
        """
        data = self._stream.read(self._chk_size)
        if not len(data):
            raise StopIteration()
        return data
