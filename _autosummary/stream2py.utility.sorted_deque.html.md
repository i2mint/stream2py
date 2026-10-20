# stream2py.utility.sorted_deque

Deque sorted by a key function.

### Classes

| [`SortedDeque`](#stream2py.utility.sorted_deque.SortedDeque)([iterable, key, maxlen])   | Deque sorted by a key function.   |
|-----------------------------------------------------------------------------------------|-----------------------------------|

### *class* stream2py.utility.sorted_deque.SortedDeque(iterable=(), key=None, maxlen=None)

Bases: [`SortedCollection`](stream2py.utility.sorted_collection.html.md#stream2py.utility.sorted_collection.SortedCollection)

Deque sorted by a key function.

Intent of SortedDeque is to efficiently search buffered data while efficiently maintaining a fixed length buffer
that is frequently popping the head and appending to the tail.

Overloaded SortedCollection methods \_\_contains_\_, index, and count due to the lack of
slicing in deques. Efficiency of said methods is still better than base deque.

Added an append method for cases where the new item to insert is known to be the last.

#### append(item)

Append item to the end and maintain key indexing.
Raise ValueError if item key is not greater than last item key.

* **Parameters:**
  **item** – item to append
* **Returns:**
  None

#### count(item)

Return number of occurrences of item

#### drop(n=1)

Remove n items from the left

* **Parameters:**
  **n**
* **Returns:**

#### find_last_gt(k)

Return last item with a key > k.  Raise ValueError if not found.
Basically a tail function with a greater than check

#### index(item)

Find the position of an item.  Raise ValueError if not found.

#### *property* maxlen

maxlen function

#### range(start, stop, step=None)

Return list of items within start and stop key range.

* **Parameters:**
  * **start** – starting key
  * **stop** – stopping key
  * **step**
* **Returns:**
  list with items in range

#### range_by_index(start_index, stop_index, step=None)

Return list of items within start and stop index range.

* **Parameters:**
  * **start_index** – starting index
  * **stop_index** – stopping index
  * **step**
* **Returns:**
  list with items in range

#### to_jdict()
