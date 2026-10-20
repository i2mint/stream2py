# stream2py.exceptions

Custom exception classes for stream2py

This module defines the exception hierarchy for stream2py, providing more
specific and informative error messages than generic Python exceptions.

### Exceptions

| [`BufferError`](#stream2py.exceptions.BufferError)               | Base exception for buffer-related errors                                       |
|----------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| [`BufferOverflowError`](#stream2py.exceptions.BufferOverflowError)       | Raised when buffer is full and auto_drop=False                                 |
| [`ConfigurationError`](#stream2py.exceptions.ConfigurationError)        | Raised when stream2py objects are misconfigured                                |
| [`InvalidDataError`](#stream2py.exceptions.InvalidDataError)          | Raised when data doesn't meet expected format or constraints                   |
| [`NoDataAvailableError`](#stream2py.exceptions.NoDataAvailableError)      | Raised when no data is available and ignore_no_item_found=False                |
| [`Stream2PyError`](#stream2py.exceptions.Stream2PyError)            | Base exception for all stream2py errors                                        |
| [`StreamAlreadyStoppedError`](#stream2py.exceptions.StreamAlreadyStoppedError) | Raised when operations require a running stream but stream has been stopped    |
| [`StreamNotStartedError`](#stream2py.exceptions.StreamNotStartedError)     | Raised when operations require a started stream but stream hasn't been started |

### *exception* stream2py.exceptions.BufferError

Bases: [`Stream2PyError`](#stream2py.exceptions.Stream2PyError)

Base exception for buffer-related errors

### *exception* stream2py.exceptions.BufferOverflowError

Bases: [`BufferError`](#stream2py.exceptions.BufferError)

Raised when buffer is full and auto_drop=False

### *exception* stream2py.exceptions.ConfigurationError

Bases: [`Stream2PyError`](#stream2py.exceptions.Stream2PyError)

Raised when stream2py objects are misconfigured

### *exception* stream2py.exceptions.InvalidDataError

Bases: [`Stream2PyError`](#stream2py.exceptions.Stream2PyError)

Raised when data doesn’t meet expected format or constraints

### *exception* stream2py.exceptions.NoDataAvailableError

Bases: [`BufferError`](#stream2py.exceptions.BufferError)

Raised when no data is available and ignore_no_item_found=False

### *exception* stream2py.exceptions.Stream2PyError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

Base exception for all stream2py errors

### *exception* stream2py.exceptions.StreamAlreadyStoppedError

Bases: [`Stream2PyError`](#stream2py.exceptions.Stream2PyError)

Raised when operations require a running stream but stream has been stopped

### *exception* stream2py.exceptions.StreamNotStartedError

Bases: [`Stream2PyError`](#stream2py.exceptions.Stream2PyError)

Raised when operations require a started stream but stream hasn’t been started
