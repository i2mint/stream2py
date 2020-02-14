stream2py
=========

Bring data streams to python, with ease.

One of the goals of the suite of i2i tools is to get from idea 2
implementation without all the fuss. We've got py2store to do that for
the storage (reading or writing) concern, and others (e.g. py2cli,
py2ws, py2dash) to take care of exposing python functions to the world
(of command line interfaces, webservices, browser dashboards, etc.).

Here, we address the stream acquisition concern. As always, we aim at
offering as-simple-as-drawing-a-simple-drawing means to get things done.

Reduce vocabulary entropy
-------------------------

One way we do this is by reducing the vocabulary entropy: We don't want
to have to think about how every specific source calls a read, or a
size, or a time to pause before reads, or what format THAT particular
sensor is encoding it's data in, having you shuffle through
documentation pages before you can figure out how to start doing the fun
stuff, which happens to be the stuff that actually produces value. And,
oh, once you figure it out, if you don't use it for a few months or
years, next time you need to do something similar, you'll have to figure
it all out again.

No. That's just a waste of time of time. Instead, we say you do that at
most once. You don't have to do it at all if the community (us) already
provided you with the their-language-to-our-consistent-language adapter
for the stream you want to hook into. And if it's something new, well
you'll have to figure it out, but you then write the adapter once, and
now you (1) can use the rest of stream2py's tools and (2) you don't have
to do it again.

Go back in time
---------------

We also address the problem of impermanence.

Think of the streams that different sensors such as audio, vibration,
video offer, or even "industrial" signals such as wifi, can bus data,
PLC, etc. They happen, and they're gone. Sure, they usually have
buffers, but these are typically just big enough to get the data from
high frequency reads -- not enough to have the time for some more
involved analysis that smart systems require.

We address this problem by

Multi readers
-------------

It often happens that you want to do more than one thing with a stream.
Say store it, visualize it in real time, and direct it to a analysis
pipeline. In order for this to be possible with no hiccups, some things
need to be taken care of. We did, so you don't have to.

Timestamp correctly
-------------------

In our extensive experience with people (the write code to store stream
data), we've noticed that many engineers, when faced with the task to
timestamp the segments of stream that they're saving, follow a design
pattern that goes like this (a) get the stream data (b) ask the system
what date/time it is (c) use that (and perhaps, just to make even more
likely for the timestamp to be interpreted incorrectly, call it the
"offset\_date")

The problem with this design pattern is that it's all pattern and no
design. It is **not** the timestamp of the beginning of the segment:
That time happened **after** the **end** of the event of the end of the
segment occurred, and even more so, **after** the system that will
timestamp and store. Further, there is a lot of wiggle room in the delay
accumulated between the actual event, and the moment we ask the system
what time it is. Sometimes it doesn't matter, but sometimes it does: For
example, if we want to align with some other timestamped data, or use
these timestamps to determine if there's gaps or overlaps between the
segments we've acquired.

Point is, stream2py will give you the tools to tackle that problem
properly. It does so by having the stream2py buffers mentioned above
keep data flow statistics that readers can then use to more precisely
timestamp what they read.
