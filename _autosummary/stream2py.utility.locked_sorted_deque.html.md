# stream2py.utility.locked_sorted_deque

Sorted Deque that handles Reader-Writer Priority

### Classes

| [`RWLockSortedDeque`](#stream2py.utility.locked_sorted_deque.RWLockSortedDeque)([iterable, key, maxlen])   |    |
|-----------------------------------------------------------------------------------------------|----|

### *class* stream2py.utility.locked_sorted_deque.RWLockSortedDeque(iterable=(), , key=None, maxlen=None)

Bases: [`RWLock`](stream2py.utility.reader_writer_lock.html.md#stream2py.utility.reader_writer_lock.RWLock)

```pycon
>>> import operator
>>> locked_deque = RWLockSortedDeque(
...     ((('plc', int(i // 10 * 10), i), f'data_{i}') for i in range(100)),
...     key=operator.itemgetter(0),
...     maxlen=100000)
>>> new_item = (('plc', 100000, 100000), 'new data')
>>> with locked_deque.writer_lock() as writer:
...     writer.append(new_item)
>>> with locked_deque.reader_lock() as reader:
...     print(reader.find_gt(('plc', 90, 91)))
...
(('plc', 90, 92), 'data_92')
>>> with locked_deque.reader_lock() as reader:
...     print(reader.find_gt(('plc', 90, 99)))
...
(('plc', 100000, 100000), 'new data')
```
