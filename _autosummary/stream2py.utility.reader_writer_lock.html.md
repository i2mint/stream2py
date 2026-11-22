# stream2py.utility.reader_writer_lock

READER-WRITER LOCK WITH PRIORITY FOR WRITERS

### Classes

| [`RWLock`](#stream2py.utility.reader_writer_lock.RWLock)()                                       | Synchronization object used in a solution of so-called second readers-writers problem.   |
|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [`RWLockTestCase`](#stream2py.utility.reader_writer_lock.RWLockTestCase)([methodName])                   | Unit tests for [`RWLock`](#stream2py.utility.reader_writer_lock.RWLock).                  |
| [`Reader`](#stream2py.utility.reader_writer_lock.Reader)(buffer_, rw_lock, init_sleep_time, ...) | Thread that copies a shared buffer under the read lock (used by the lock tests).         |
| [`Writer`](#stream2py.utility.reader_writer_lock.Writer)(buffer_, rw_lock, init_sleep_time, ...) | Thread that appends to a shared buffer under the write lock (used by the lock tests).    |

### *class* stream2py.utility.reader_writer_lock.RWLock

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Synchronization object used in a solution of so-called second
readers-writers problem. In this problem, many readers can simultaneously
access a share, and a writer has an exclusive access to this share.
Additionally, the following constraints should be met:

1. no reader should be kept waiting if the share is currently opened for
   : reading unless a writer is also waiting for the share,
2. no writer should be kept waiting for the share longer than absolutely
   : necessary.

The implementation is based on [1, secs. 4.2.2, 4.2.6, 4.2.7]
with a modification – adding an additional lock (C{self._\_readers_queue})
– in accordance with [2].

Sources:
[1] A.B. Downey: “The little book of semaphores”, Version 2.1.5, 2008
[2] P.J. Courtois, F. Heymans, D.L. Parnas:

```default
"Concurrent Control with 'Readers' and 'Writers'",
Communications of the ACM, 1971 (via [3])
```

[3] [http://en.wikipedia.org/wiki/Readers-writers_problem](http://en.wikipedia.org/wiki/Readers-writers_problem)

#### reader_acquire()

Acquire the lock for reading (shared).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### reader_release()

Release a read lock.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### writer_acquire()

Acquire the lock for writing (exclusive).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### writer_release()

Release the write lock.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* stream2py.utility.reader_writer_lock.RWLockTestCase(methodName='runTest')

Bases: [`TestCase`](https://docs.python.org/3/library/unittest.html#unittest.TestCase)

Unit tests for [`RWLock`](#stream2py.utility.reader_writer_lock.RWLock).

#### test_many_writers_priority()

Check many writers priority.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### test_readers_nonexclusive_access()

Check readers nonexclusive access.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### test_writer_priority()

Check writer priority.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### test_writers_exclusive_access()

Check writers exclusive access.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* stream2py.utility.reader_writer_lock.Reader(buffer_, rw_lock, init_sleep_time, sleep_time)

Bases: [`Thread`](https://docs.python.org/3/library/threading.html#threading.Thread)

Thread that copies a shared buffer under the read lock (used by the lock tests).

#### buffer_read

a copy of a the buffer read while in critical section

#### entry_time

Time of entry to the critical section

#### exit_time

Time of exit from the critical section

#### run()

Thread body: wait, take the lock, do the work, release.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* stream2py.utility.reader_writer_lock.Writer(buffer_, rw_lock, init_sleep_time, sleep_time, to_write)

Bases: [`Thread`](https://docs.python.org/3/library/threading.html#threading.Thread)

Thread that appends to a shared buffer under the write lock (used by the lock tests).

#### entry_time

Time of entry to the critical section

#### exit_time

Time of exit from the critical section

#### run()

Thread body: wait, take the lock, do the work, release.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)
