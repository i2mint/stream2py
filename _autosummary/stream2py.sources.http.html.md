# stream2py.sources.http

## HTTP Response streaming reader with no external dependencies

### Classes

| [`HTTPResponseReader`](#stream2py.sources.http.HTTPResponseReader)(url, \*[, method, ...])   | Source reader that streams the raw bytes of an HTTP response.   |
|-----------------------------------------------------------------------------------------------|-----------------------------------------------------------------|

### *class* stream2py.sources.http.HTTPResponseReader(url, , method='GET', headers=None, body='', response_format='bytes', response_read_args=(), encoding='')

Bases: [`SourceReader`](stream2py.source_reader.html.md#stream2py.source_reader.SourceReader)

Source reader that streams the raw bytes of an HTTP response.

#### close()

Close the resource.

#### *property* info *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)*

Provides a dict with init kwargs and read status

```pycon
>>> from pprint import pprint
>>> source = HTTPResponseReader('http://zombo.com')
>>> pprint(source.info)
{'url': 'http://zombo.com',
 'n_bytes_read': 0,
 'init_kwargs': {'method': 'GET,
                 'headers': {},
                 'body': None,
                 'response_format': 'bytes'}}
```

* **Returns:**
  dict

#### key(data)

Returns a slice of the data retrieved.

* **Parameters:**
  **data** – (start_index, end_index)
* **Return type:**
  [`ComparableType`](stream2py.utility.typing_hints.html.md#stream2py.utility.typing_hints.ComparableType)
* **Returns:**
  Union[str, bytes]

#### open()

Open the resource.

#### read()

Returns a chunk of raw binary data.
