.. graphviz::

    digraph {
        rankdir=LR;
        "SourceReader" [shape=cds]
        "StreamBuffer" [shape=box3d]
        "SourceReader" -> "StreamBuffer" -> "BufferReader1";
        "StreamBuffer" -> "BufferReader2";
        "StreamBuffer" -> "BufferReader3";
    }
