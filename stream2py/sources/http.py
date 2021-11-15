"""
HTTP Response streaming reader with no external dependencies
--------------
.. autoclass:: stream2py.sources.net.HTTPResponseReader()
    :members:
    :show-inheritance:

    .. automethod:: __init__

"""

import urllib.request
from typing import Union, Optional
import time

from stream2py import SourceReader
from stream2py.utility.typing_hints import ComparableType


class HTTPResponseReader(SourceReader):
    _request: urllib.request.Request
    _n_bytes_read: int
    _init_kwargs: dict
    _url: str
    _response = ''

    def __init__(
        self,
        url,
        *,
        method: str = 'GET',
        headers: Optional[dict] = None,
        body: Union[str, bytes] = '',
        response_format: str = 'bytes',
        response_read_args: tuple = (),
        encoding: str = '',
    ):
        """
        :param method: The HTTP method to use.
        :param headers: The HTTP headers to pass with the request.
        :param body: The body to send with the request. Must be a string or bytes (JSON bodies should be passed through json.dumps)
        :param response_format: Format to map the response to. Accepts 'bytes' or 'str' (defaults to 'bytes')
        """
        headers = headers or {}
        self._init_kwargs = dict(
            method=method,
            headers=headers,
            body=body,
            response_format=response_format,
            encoding=encoding,
        )
        self.data = None
        if method.upper() == 'GET':
            body = None

        self._url = url
        self._n_bytes_read = 0
        self._request = urllib.request.Request(
            url, data=body, headers=headers, method=method
        )
        if response_read_args is None:
            response_read_args = ()
        if not isinstance(response_read_args, tuple):
            response_read_args = (response_read_args,)
        self.response_read_args = response_read_args

    @property
    def info(self) -> dict:
        """
        Provides a dict with init kwargs and read status

        >>> from pprint import pprint
        >>> source = HTTPResponseReader('http://zombo.com')
        >>> pprint(source.info) # doctest: +SKIP
        {'url': 'http://zombo.com',
         'n_bytes_read': 0,
         'init_kwargs': {'method': 'GET,
                         'headers': {},
                         'body': None,
                         'response_format': 'bytes'}}

        :return: dict
        """
        return {
            'url': self._url,
            'n_bytes_read': self._n_bytes_read,
            'init_kwargs': self._init_kwargs,
        }

    def key(self, data) -> ComparableType:
        """
        Returns a slice of the data retrieved.

        :param data: (start_index, end_index)
        :return: Union[str, bytes]
        """
        return data
        # return self._data[data[0]:data[1]]

    def open(self):
        request = urllib.request.Request(
            self._url, headers=self._init_kwargs['headers']
        )
        self._response = urllib.request.urlopen(request)

    def close(self):
        if self._response:
            self._response.__exit__()
            self._response = None

    def read(self):
        """Returns a chunk of raw binary data.
        """
        encoding = self._init_kwargs.get('encoding')
        result = self._response.read(*self.response_read_args)
        timestamp = time.time()
        if encoding:
            result = result.decode(encoding)
        return timestamp, result


def _test_run_HTTPResponseReader(url, **kwargs):
    """Run HTTPResponseReader and print some stuff

    :param readerClass: HTTPResponseReader class or subclass
    """
    from pprint import pprint

    output = ''

    source = HTTPResponseReader(url, **kwargs)
    pprint(source.info)
    try:
        source.open()
        pprint(source.info)
        i = 0
        while i < 600:
            data = source.read(10)
            if not data:
                break
            i += 1
            output += data

    finally:
        source.close()
        pprint(source.info)
        pprint(output)


if __name__ == '__main__':
    _test_run_HTTPResponseReader('https://zombo.com', encoding='utf-8')
