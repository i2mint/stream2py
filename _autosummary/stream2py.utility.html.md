# stream2py.utility

Low-level building blocks used by stream2py’s buffers and readers.

These are general-purpose data structures and synchronization primitives that do not
depend on stream2py objects themselves:

- [`stream2py.utility.sorted_collection`](stream2py.utility.sorted_collection.html.md#module-stream2py.utility.sorted_collection) – a sorted sequence with bisect-based lookup
- [`stream2py.utility.sorted_deque`](stream2py.utility.sorted_deque.html.md#module-stream2py.utility.sorted_deque) – a bounded sorted deque
- [`stream2py.utility.locked_sorted_deque`](stream2py.utility.locked_sorted_deque.html.md#module-stream2py.utility.locked_sorted_deque) – a sorted deque guarded by a lock
- [`stream2py.utility.reader_writer_lock`](stream2py.utility.reader_writer_lock.html.md#module-stream2py.utility.reader_writer_lock) – a multi-reader/single-writer lock
- [`stream2py.utility.typing_hints`](stream2py.utility.typing_hints.html.md#module-stream2py.utility.typing_hints) – shared type aliases

### Modules

| [`locked_sorted_deque`](stream2py.utility.locked_sorted_deque.html.md#module-stream2py.utility.locked_sorted_deque)   | Sorted Deque that handles Reader-Writer Priority   |
|---------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|
| [`reader_writer_lock`](stream2py.utility.reader_writer_lock.html.md#module-stream2py.utility.reader_writer_lock)     | READER-WRITER LOCK WITH PRIORITY FOR WRITERS       |
| [`sorted_collection`](stream2py.utility.sorted_collection.html.md#module-stream2py.utility.sorted_collection)       | Sequence sorted by a key function.                 |
| [`sorted_deque`](stream2py.utility.sorted_deque.html.md#module-stream2py.utility.sorted_deque)                 | Deque sorted by a key function.                    |
| [`typing_hints`](stream2py.utility.typing_hints.html.md#module-stream2py.utility.typing_hints)                 | Typing hints                                       |
