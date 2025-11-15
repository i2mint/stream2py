"""Custom exception classes for stream2py

This module defines the exception hierarchy for stream2py, providing more
specific and informative error messages than generic Python exceptions.
"""


class Stream2PyError(Exception):
    """Base exception for all stream2py errors"""


class StreamNotStartedError(Stream2PyError):
    """Raised when operations require a started stream but stream hasn't been started"""


class StreamAlreadyStoppedError(Stream2PyError):
    """Raised when operations require a running stream but stream has been stopped"""


class BufferError(Stream2PyError):
    """Base exception for buffer-related errors"""


class BufferOverflowError(BufferError):
    """Raised when buffer is full and auto_drop=False"""


class NoDataAvailableError(BufferError):
    """Raised when no data is available and ignore_no_item_found=False"""


class InvalidDataError(Stream2PyError):
    """Raised when data doesn't meet expected format or constraints"""


class ConfigurationError(Stream2PyError):
    """Raised when stream2py objects are misconfigured"""
