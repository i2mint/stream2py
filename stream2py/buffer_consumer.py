"""
Work in progress. Use as example to construct your own until this is finalized with a standard api.

Abstract classes to make asynchronous consumers of BufferReaders and StreamBuffers.
"""

from abc import ABCMeta, abstractmethod

from contextlib import suppress
import logging
import threading
import time

from stream2py import BufferReader, StreamBuffer
from stream2py.utility.typing_hints import Union

logger = logging.getLogger(__name__)


class BufferReaderConsumer(threading.Thread, metaclass=ABCMeta):
    """Call reader_handler function with reader at defined time intervals between calls"""

    def __init__(
        self,
        buffer_reader: BufferReader,
        interval: Union[int, float],
        logging_enabled: bool = False,
    ):
        """

        :param buffer_reader: BufferReader created from a StreamBuffer
        :param interval: seconds between reader_handler calls
        :param logging_enabled: log debug messages using logging module
        """
        threading.Thread.__init__(self, daemon=True)
        assert isinstance(buffer_reader, BufferReader)
        self.buffer_reader = buffer_reader
        self.interval = interval
        self.stop_event = threading.Event()
        self.logging_enabled = logging_enabled

    def stop(self):
        """Sets stop event and waits for thread to finish"""
        self.stop_event.set()
        if self.logging_enabled:
            logger.debug(f'Consumer stopping... {self.__class__.__name__}')
        self.join()

    def run(self):
        """Calls self.reader_handler in a loop while sleeping for self.interval seconds after each call until stop event
        is set or Exception is raised by self.reader_handler"""
        if self.logging_enabled:
            logger.debug(f'Consumer starting! {self.__class__.__name__}')
        try:
            while not self.stop_event.is_set():
                self.reader_handler(self.buffer_reader)
                if self.interval > 0:
                    time.sleep(self.interval)
        finally:
            with suppress(Exception):
                self.stop()
        if self.logging_enabled:
            logger.debug(f'Consumer stopped! {self.__class__.__name__}')

    @abstractmethod
    def reader_handler(self, buffer_reader: BufferReader):
        """Implements how to read from buffer and what to do with the data"""
        raise NotImplementedError

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class StreamBufferConsumer(threading.Thread, metaclass=ABCMeta):
    def __init__(
        self,
        stream_buffer: StreamBuffer,
        interval: Union[int, float],
        logging_enabled: bool = False,
    ):
        """

        :param stream_buffer: a StreamBuffer
        :param interval: seconds between stream_buffer_handler calls
        :param logging_enabled: log debug messages using logging module
        """
        threading.Thread.__init__(self, daemon=True)
        assert isinstance(stream_buffer, StreamBuffer)
        self.stream_buffer = stream_buffer
        self.interval = interval
        self.stop_event = threading.Event()
        self.logging_enabled = logging_enabled

    def stop(self):
        """Sets stop event and waits for thread to finish"""
        self.stop_event.set()
        if self.logging_enabled:
            logger.debug(f'Consumer stopping... {self.__class__.__name__}')
        self.join()

    def run(self):
        """Calls self.reader_handler in a loop while sleeping for self.interval seconds after each call until stop event
        is set or Exception is raised by self.stream_buffer_handler"""
        if self.logging_enabled:
            logger.debug(f'Consumer starting! {self.__class__.__name__}')
        try:
            while not self.stop_event.is_set():
                self.stream_buffer_handler(self.stream_buffer)
                time.sleep(self.interval)
        finally:
            with suppress(Exception):
                self.stop()
        if self.logging_enabled:
            logger.debug(f'Consumer stopped! {self.__class__.__name__}')

    @abstractmethod
    def stream_buffer_handler(self, stream_buffer: StreamBuffer):
        """Implements how to read from buffer and what to do with the data"""
        raise NotImplementedError

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
