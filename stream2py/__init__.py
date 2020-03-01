"""
API Documentation
=================

.. graphviz::

    digraph {
        rankdir=LR;
        "SourceReader" [shape=cds]
        "StreamBuffer" [shape=box3d]
        "SourceReader" -> "StreamBuffer" -> "BufferReader1";
        "StreamBuffer" -> "BufferReader2";
        "StreamBuffer" -> "BufferReader3";
    }

Classes
-------
.. autoclass:: stream2py.SourceReader
    :members:

.. autoclass:: stream2py.StreamBuffer()
    :members:

    .. automethod:: __init__

.. autoclass:: stream2py.BufferReader()
    :members:

TODO
----
* doctest for each exposed method with sphinx.ext.doctest's testsetup and testcleanup to clearly show usage
* reduce the complexity of the main doctest of each class

"""

from stream2py.source_reader import *
from stream2py.buffer_reader import *
from stream2py.stream_buffer import *
