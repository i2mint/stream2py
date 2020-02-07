
# Stream iterator

From a stream get:
- An object that behaves like an (unbounded) iterator, fed by a stream.
- An object that behaves like an (unbounded) list, but without access to stuff that's not in the buffer anymore.
- An object that behaves like an (unbounded) list, with access to all the data since the stream was 
turned on -- sourcing the data from the buffer if present, or from stored data if not.

# Get data from stream when ever I choose

## Give me data I don't have yet: Both pull and push options

## Full contents
Dynamically get a copy of the full contents of a stream buffer

## Most recent
Only a most recent subset of it (of a given size, duration, or cardinality).

## Any range present in buffer
Grab any range of data that's in the buffer. Provide various types of interval specification units, 
such as datetime timestamps, numerical timestamps, integer indices, etc.

## Any range 
Take from buffer if present, or from stored timestamped signals if not.

# Store streams with precise timestamps

