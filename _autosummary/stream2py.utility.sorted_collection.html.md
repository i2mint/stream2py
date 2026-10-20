# stream2py.utility.sorted_collection

Sequence sorted by a key function.

### Classes

| [`SortedCollection`](#stream2py.utility.sorted_collection.SortedCollection)([iterable, key])   | Sequence sorted by a key function.   |
|--------------------------------------------------------------------------------------|--------------------------------------|

### *class* stream2py.utility.sorted_collection.SortedCollection(iterable=(), key=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Sequence sorted by a key function.

SortedCollection() is much easier to work with than using bisect() directly.
It supports key functions like those use in sorted(), min(), and max().
The result of the key function call is saved so that keys can be searched
efficiently.

Instead of returning an insertion-point which can be hard to interpret, the
five find-methods return a specific item in the sequence. They can scan for
exact matches, the last item less-than-or-equal to a key, or the first item
greater-than-or-equal to a key.

Once found, an item’s ordinal position can be located with the index() method.
New items can be added with the insert() and insert_right() methods.
Old items can be deleted with the remove() method.

The usual sequence methods are provided to support indexing, slicing,
length lookup, clearing, copying, forward and reverse iteration, contains
checking, item counts, item removal, and a nice looking repr.

Finding and indexing are O(log n) operations while iteration and insertion
are O(n).  The initial sort is O(n log n).

The key function is stored in the ‘key’ attibute for easy introspection or
so that you can assign a new key function (triggering an automatic re-sort).

In short, the class was designed to handle all of the common use cases for
bisect but with a simpler API and support for key functions.

```pycon
>>> from pprint import pprint
>>> from operator import itemgetter
```

```pycon
>>> s = SortedCollection(key=itemgetter(2))
>>> for record in [
...         ('roger', 'young', 30),
...         ('angela', 'jones', 28),
...         ('bill', 'smith', 22),
...         ('david', 'thomas', 32)]:
...     s.insert(record)
```

```pycon
>>> pprint(list(s))         # show records sorted by age
[('bill', 'smith', 22),
 ('angela', 'jones', 28),
 ('roger', 'young', 30),
 ('david', 'thomas', 32)]
```

```pycon
>>> s.find_le(29)           # find oldest person aged 29 or younger
('angela', 'jones', 28)
>>> s.find_lt(28)           # find oldest person under 28
('bill', 'smith', 22)
>>> s.find_gt(28)           # find youngest person over 28
('roger', 'young', 30)
```

```pycon
>>> r = s.find_ge(32)       # find youngest person aged 32 or older
>>> s.index(r)              # get the index of their record
3
>>> s[3]                    # fetch the record at that index
('david', 'thomas', 32)
```

```pycon
>>> s.key = itemgetter(0)   # now sort by first name
>>> pprint(list(s))
[('angela', 'jones', 28),
 ('bill', 'smith', 22),
 ('david', 'thomas', 32),
 ('roger', 'young', 30)]
```

#### count(item)

Return number of occurrences of item

#### find(k)

Return first item with a key == k.  Raise ValueError if not found.

#### find_ge(k)

Return first item with a key >= equal to k.  Raise ValueError if not found

#### find_gt(k)

Return first item with a key > k.  Raise ValueError if not found

#### find_le(k)

Return last item with a key <= k.  Raise ValueError if not found.

#### find_lt(k)

Return last item with a key < k.  Raise ValueError if not found.

#### index(item)

Find the position of an item.  Raise ValueError if not found.

#### insert(item)

Insert a new item.  If equal keys are found, add to the left

#### insert_right(item)

Insert a new item.  If equal keys are found, add to the right

#### *property* key

key function

#### remove(item)

Remove first occurence of item.  Raise ValueError if not found
