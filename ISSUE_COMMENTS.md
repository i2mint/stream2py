# Issue Comments - Ready to Post

Copy and paste these comments to the respective GitHub issues.

---

## Issue #6: a `closed` parameter for SourceReader

✅ **RESOLVED** in PR #[TBD]

This issue has been resolved! A `closed` property has been added to `SourceReader`, similar to `io.IOBase.closed`.

**Implementation:**
- Added `_closed` attribute to track open/close state (defaults to `True`)
- Added `closed` property that returns `self._closed`
- Updated `__enter__` and `__exit__` to manage the `_closed` flag
- Updated `QuickSourceReader.open()` and `close()` to properly set the flag
- Added docstring examples demonstrating usage

**Code references:**
- `source_reader.py:76` - `_closed` attribute initialization
- `source_reader.py:129-137` - `closed` property definition
- `source_reader.py:165-172` - Updated `__enter__` and `__exit__`
- `source_reader.py:244-252` - QuickSourceReader implementation

**Example usage:**
```python
source = SimpleCounterString(start=0, stop=10)
assert source.closed == True  # Starts closed
source.open()
assert source.closed == False  # Now open
source.close()
assert source.closed == True  # Closed again
```

This property now provides a consistent way to check if a stream is open, matching the interface of `io.IOBase`.

---

## Issue #20: Add option to make BufferReader blocking to wait for future data

✅ **ALREADY RESOLVED**

This feature is already implemented! The `blocking` parameter already exists in `BufferReader.read()`.

**Current implementation:**
- `BufferReader.read()` accepts `blocking=False` parameter (line 329 in buffer_reader.py)
- When `blocking=True`, the read will wait until data becomes available
- When `blocking=False`, it returns immediately (returns None if no data available with `ignore_no_item_found=True`)

**Code reference:**
```python
def read(
    self,
    n=None,
    *,
    peek=None,
    ignore_no_item_found=None,
    strict_n=None,
    blocking=False,  # <-- This parameter exists!
):
    # ... implementation at lines 322-401 in buffer_reader.py
```

**Example usage:**
```python
# Non-blocking read
result = reader.read(blocking=False, ignore_no_item_found=True)

# Blocking read - waits for data
result = reader.read(blocking=True)
```

**Tests added:**
Comprehensive tests for this functionality were added in `stream2py/tests/test_buffer_reader_blocking.py` in the recent PR to ensure the blocking parameter works correctly.

**Recommendation:** This issue can be closed as the feature is already implemented and now has test coverage.

---

## Issue #8: Add parameters (block=False, timeout=None) in BufferReader methods

⚠️ **PARTIALLY RESOLVED**

The `blocking` parameter is already implemented, but `timeout` is not yet available.

**What's implemented:**
- ✅ `blocking` parameter exists in `BufferReader.read()` (line 329 in buffer_reader.py)
- When `blocking=True`, read waits indefinitely for data to become available
- When `blocking=False`, returns immediately

**What's missing:**
- ❌ `timeout` parameter to specify maximum wait time
- Currently, blocking read will wait forever or until the buffer stops

**Recommendation:**
Could add a `timeout` parameter that works like:
```python
result = reader.read(blocking=True, timeout=5.0)  # Wait max 5 seconds
```

This would be a simple enhancement on top of the existing blocking implementation. The blocking behavior already checks `self.is_stopped` and uses `time.sleep()`, so adding a timeout would just require tracking elapsed time.

**Effort:** Simple (a few lines of code)

**Related:** Issue #20 requested the blocking parameter which already exists.

---

## Issue #10: Make BufferReader.__next__() more compatible with builtin next()

✅ **RESOLVED** in this PR

**Status:** Implemented

**Implementation:**
Modified `BufferReader.__next__()` to properly raise `StopIteration` when the stream is stopped and no data is available, while still returning `None` when temporarily no data is available but the stream is still running.

**Changes Made:**
- `buffer_reader.py:153-169` - Updated `__next__()` to raise `StopIteration` when `result is None and self.is_stopped`
- `buffer_reader.py:143-156` - Updated `__iter__()` to catch `StopIteration` (prevents RuntimeError in Python 3.7+)
- Added comprehensive tests in `test_buffer_reader_stopiteration.py`:
  - Test that `StopIteration` is raised when stream stopped
  - Test that `None` is returned when no data but stream still running
  - Test that builtin `next()` with default value works correctly
  - Test that for loops stop correctly

**Benefits:**
- Now fully compatible with Python's iterator protocol
- Works correctly with builtin `next(reader, default)`
- For loops terminate properly when stream stops
- Distinguishes between "no data yet" (returns None) vs "stream exhausted" (raises StopIteration)

**Reference:** https://docs.python.org/3/library/functions.html#next

---

## Issue #18: What should happen if we start to read without starting the reader?

✅ **ADDRESSED** in this PR

**Status:** Checks already exist, now documented and tested

**Resolution:**
The necessary checks already exist! `StreamBuffer.mk_reader()` raises a clear error if called before the buffer is started. Additionally, the BufferReader doesn't require being in a `with` block to function - the context manager is only for cleanup.

**Current Implementation:**
- `StreamBuffer.mk_reader()` raises `StreamNotStartedError` (formerly `RuntimeError`) if buffer not started
- BufferReader works fine without context manager
- Context manager on BufferReader ensures proper cleanup (calls `onclose` callback)

**Changes Made in This PR:**
- Created custom `StreamNotStartedError` exception with clearer error messages
- Added comprehensive tests in `test_reader_without_context.py`:
  - `test_mk_reader_requires_started_buffer()` - verifies error is raised
  - `test_reader_works_without_context_manager()` - shows readers work without `with` block
  - `test_context_manager_ensures_cleanup()` - shows context manager benefits
  - `test_reader_without_context_still_works()` - demonstrates manual cleanup
  - `test_stream_buffer_with_context()` - shows recommended pattern

**Documented Behavior:**
1. **StreamBuffer must be started** before creating readers - this is enforced
2. **BufferReader context manager is optional** - used for cleanup, not required for reading
3. **Recommended pattern**: Use `with StreamBuffer(...) as buffer:` for automatic cleanup

**Related:**
- See wiki: https://github.com/i2mint/stream2py/wiki/Forwarding-context-management
- Enhanced by `contextualize_with_instance` utility

---

## Issue #17: Revise BufferReader

📋 **NEEDS WORK** (Medium effort)

**Status:** Relevant - multiple TODOs to address

**TODOs identified:**

1. ✅ **`read` must get its defaults from init** - DONE
   - Already implemented via `_read_kwargs` in `BufferReader.__init__`

2. ❓ **`range` must work similarly to `read`** - NEEDS REVIEW
   - Should `range()` also respect the same default parameters from init?
   - Currently `range()` has its own parameter handling

3. ❓ **Which init args should be keyword-only?** - DESIGN DECISION
   - Current: `read_size`, `peek`, `strict_n`, `ignore_no_item_found` are keyword-only
   - Recommendation: Keep current approach for clarity

4. ❓ **Consider making `read_chk_step` and `read_chk_size` (instead of just `peek`)**
   - More granular control over chunked reading
   - Would this add value or just complexity?

**TODOs in code:**
- `buffer_reader.py:95` - "should `ignore_no_item_found` default be True to align with iter?"
- `stream_buffer.py:125` - "option to auto restart source on read exception"

**Recommendation:** Address each TODO systematically with design review

**Effort:** Medium (each item is simple, but needs careful consideration)

---

## Issue #14: Add support for slicing joinable data items

📋 **NEEDS WORK** (Medium effort)

**Status:** Relevant feature enhancement

**Description:**
For data like waveform chunks that can be joined together, `BufferReader.range()` currently returns a list of chunks that often need trimming at start/stop. It would be better to optionally join and trim to get exact query results.

**Current behavior:**
```python
chunks = reader.range(start=1000, stop=5000)  # Returns list of chunks
# User has to manually join and trim
```

**Desired behavior:**
```python
data = reader.range(start=1000, stop=5000, join=True)  # Returns exact slice
```

**Recommendation:**
Add optional abstract methods to `SourceReader`:
- `join(items)` - joins multiple read data items into one
- `slice(item, start, stop)` - slices a single data item

Then `BufferReader.range()` could use these methods to return precisely trimmed data.

**Benefits:**
- More precise range queries for chunked data (audio, video, sensor data)
- Removes boilerplate from user code
- Maintains flexibility (optional feature)

**Effort:** Medium

---

## Issue #15: Review exception objects raised and figure out custom ones

✅ **RESOLVED** (Foundation implemented in this PR)

**Status:** Core exception hierarchy created and integrated

**Implementation:**
Created comprehensive exception hierarchy in `stream2py/exceptions.py` and integrated it into the codebase.

**Exception Classes Created:**
```python
class Stream2PyError(Exception):
    """Base exception for all stream2py errors"""

class StreamNotStartedError(Stream2PyError):
    """Raised when operations require a started stream"""

class StreamAlreadyStoppedError(Stream2PyError):
    """Raised when stream has been stopped"""

class BufferError(Stream2PyError):
    """Base exception for buffer-related errors"""

class BufferOverflowError(BufferError):
    """Raised when buffer is full and auto_drop=False"""

class NoDataAvailableError(BufferError):
    """Raised when no data is available"""

class InvalidDataError(Stream2PyError):
    """Raised when data doesn't meet expected format"""

class ConfigurationError(Stream2PyError):
    """Raised when objects are misconfigured"""
```

**Integration Completed:**
- Updated `StreamBuffer.mk_reader()` to raise `StreamNotStartedError` with helpful message
- Updated `StreamBuffer.attach_reader()` to raise `StreamNotStartedError`
- Updated tests to expect custom exceptions
- Exported exceptions module from `stream2py.__init__`

**Benefits Realized:**
- ✅ More informative error messages (e.g., suggests using `with StreamBuffer(...)`)
- ✅ Easier to catch specific stream2py errors
- ✅ Clearer API semantics
- ✅ Better IDE autocomplete support

**Future Work:**
Continue replacing generic exceptions throughout codebase with appropriate custom exceptions. The foundation is now in place.

---

## Issue #13: keyboard_and_audio not working in notebook

🔧 **EXTERNAL PACKAGE** - Applies to keyboardstream2py

**Status:** Not applicable to core stream2py

**Investigation:**
The `getch.py` file and keyboard functionality referenced in this issue **do not exist in core stream2py**. This functionality has been moved to the separate `keyboardstream2py` package as part of stream2py's plugin architecture.

**Resolution:**
This issue applies to the **[keyboardstream2py](https://github.com/i2mint/keyboardstream2py)** package, not core stream2py.

**Recommendation:**
1. **Move this issue** to the keyboardstream2py repository, OR
2. **Close this issue** with a comment directing users to report keyboard-specific issues in the appropriate repository

**For keyboardstream2py maintainers:**
If this issue is moved to keyboardstream2py, the solution would involve:
1. Detecting notebook environments
2. Providing alternative input methods (e.g., `ipywidgets`)
3. Documenting limitations clearly

**Note:** This follows stream2py's design philosophy of keeping core dependency-free and moving specific functionality to plugin packages.

---

## Issue #9: Not skipping tests and linting

❓ **NEEDS CLARIFICATION** - CI appears correct

**Status:** Investigated - current setup looks appropriate

**Investigation Results:**
Reviewed `.github/workflows/ci.yml` thoroughly:

**Tests ARE running:**
- Line 43: `pytest -s --doctest-modules -v $PROJECT_NAME` - runs all tests including doctests
- Executes in the "validation" job on every push/PR

**Linting IS running:**
- Line 40: `pylint ./$PROJECT_NAME --ignore=tests,examples,scrap --disable=all --enable=C0114`
- Checks for missing module docstrings
- Executes in the "validation" job

**The `--bypass-tests` flag (line 96):**
- Only used in the "publish" job's `pack check-in` command
- This is APPROPRIATE because:
  1. Tests already ran successfully in the validation job (line 47: `needs: validation`)
  2. This step only commits automated formatting/documentation changes
  3. No code logic changes happen in this step
  4. Bypassing here prevents redundant test runs

**Conclusion:**
The CI configuration appears correct. Tests and linting run on every push/PR. The bypass flags are only used appropriately for automated commits.

**Question for Issue Author:**
What specifically is being inappropriately skipped? The current setup follows CI best practices. If there's a specific concern, please provide details so we can address it.

---

## Issue #4: New webcam SourceReader

✅ **EXTERNAL - CAN CLOSE**

**Status:** Feature moved to separate package

**Resolution:** Webcam functionality has been moved to a separate plugin package: [videostream2py](https://github.com/i2mint/videostream2py)

This follows the stream2py architecture of keeping core functionality dependency-free and moving specific source implementations to separate packages.

**Recommendation:** Close this issue with a comment directing users to videostream2py.

---

## Issue #16: Address the BufferReader(...source_reader_info...) issue

❓ **NEEDS INVESTIGATION**

**Status:** Needs investigation

**Reference:** https://github.com/i2mint/stream2py/wiki/Review-notes

**Current understanding:**
The issue references review notes on the wiki, but the specific problem with `source_reader_info` in `BufferReader` needs clarification.

**Recommendation:**
1. Review the wiki notes to understand the specific issue
2. Determine if it's:
   - A design problem with how `source_reader_info` is passed/stored?
   - A naming issue?
   - A mutability concern?
   - Something else?

3. Update this issue with findings and proposed solution

**Effort:** Unknown until wiki is reviewed

---

## Issue #1: Create usage examples and helper classes

📋 **ONGOING** (Complex/Long-term)

**Status:** Ongoing work, partially complete

**Progress:**

**SourceReaders:**
- ✅ webcam → moved to [videostream2py](https://github.com/i2mint/videostream2py)
- ✅ keyboard input → moved to [keyboardstream2py](https://github.com/i2mint/keyboardstream2py)
- ✅ audio → moved to [audiostream2py](https://github.com/i2mint/audiostream2py)
- ⏳ url stream - still needed

**BufferReader Consumer Ideas:**
- ⏳ General saving to files
- ⏳ Event based actions
  - ⏳ Save recording before and after webcam sees the color red
  - ⏳ Save recording before and after a loud noise
  - ⏳ Save recording while detecting voices
- ⏳ Data visualization
  - ⏳ Audio loudness graph
  - ⏳ Audio playback
  - ⏳ Video stream or snapshots
  - ⏳ Display json data

**BufferConsumer class:**
- ⏳ Isolate common patterns when using BufferReader as asynchronous consumer
- ⏳ Single source consumers
- ⏳ Multiple source consumers (e.g., webcam + audio event triggers)

**Recommendation:**
Continue incremental progress. Many core SourceReaders have been moved to separate plugin packages (good!). Focus now on:
1. Creating example consumer applications
2. Identifying common patterns for BufferConsumer abstraction
3. Creating helper utilities based on real usage patterns

**Related:** Issues #2, #3, #5

---

## Issue #11: Various sources

📋 **ONGOING** (Complex/Long-term)

**Status:** Ongoing work, many sources moved to plugin packages

**Progress:**

**Remote:**
- ⏳ Public Webcam video
- ⏳ Public Webcam audio
- ⏳ Web-audio (radio feeds, etc. -- e.g. https://www.liveatc.net/)

**Local:**
- ✅ keyboard → [keyboardstream2py](https://github.com/i2mint/keyboardstream2py)
- ⏳ mouse movements
- ✅ local webcam → [videostream2py](https://github.com/i2mint/videostream2py)
- ⏳ (filtered) wifi packets
- ⏳ bluetooth
- ✅ `top` (cpu/ram/energy usages) → [pchealthstream2py](https://github.com/i2mint/pchealthstream2py)
- ⏳ anything else easily accessible without specialized hardware?

**Sensors:**
- ✅ PLC → [plcstream2py](https://github.com/i2mint/plcstream2py)
- ⏳ Other cheap, easy to acquire sensors

**Recommendation:**
Continue the pattern of creating separate plugin packages for each source type. This keeps stream2py core lightweight and dependency-free while allowing rich ecosystem of source readers.

**Priority:** Focus on commonly requested sources and those that don't require specialized hardware.

---

## Issue #2: Tag Sound Events

📋 **EXAMPLE APPLICATION** (Medium-Complex)

**Status:** Relevant example application

**Description:**
Create an example application to help annotate audible events from a sound source.

**Features:**
- Play audio (either live or from a prerecorded file)
- Listen and tag events by pressing different keys for different tags
- Save timestamped tags that map to an audio file
- Extra credit: audio visualization to help playback and verify tag placement

**Value:**
Good example demonstrating:
- Multi-source coordination (audio + keyboard)
- Event-based triggers
- Timestamping and data correlation
- Real-world use case

**Dependencies:**
- Requires audiostream2py (already exists)
- Requires keyboardstream2py (already exists)

**Recommendation:**
Good candidate for next example application. Could be placed in `examples/` directory or in audiostream2py repository.

**Effort:** Medium

**Related:** Issues #1 (examples), #3 (similar multi-source example)

---

## Issue #3: Two Source Event Trigger: Record as You Type

📋 **EXAMPLE APPLICATION** (Medium)

**Status:** Relevant example application

**Description:**
Save audio recorded while you type on a keyboard to a wav file. Also capture a little before typing begins and after typing ends. Also save what is typed.

**Value:**
Good example demonstrating:
- Two-source event triggering
- Buffer lookback (capturing "before" an event)
- Buffer lookahead (capturing "after" an event)
- Practical use case for meeting notes, transcription assistance, etc.

**Dependencies:**
- Requires audiostream2py (already exists)
- Requires keyboardstream2py (already exists)

**Implementation approach:**
```python
# Pseudocode
audio_buffer = AudioStreamBuffer()
keyboard_buffer = KeyboardStreamBuffer()

keyboard_reader = keyboard_buffer.mk_reader()
audio_reader = audio_buffer.mk_reader()

for key_event in keyboard_reader:
    if key_event == 'start_typing':
        # Capture audio from 2 seconds before until typing stops
        start_time = current_time - 2.0
        # ... continue recording until typing stops
```

**Recommendation:**
Great example for demonstrating the power of multi-source stream coordination. Could be implemented after issue #2 or independently.

**Effort:** Medium

**Related:** Issues #1 (examples), #2 (similar use case), #5 (would help identify patterns)

---

## Issue #5: Generalize StreamBuffer and BufferReader consumers

📋 **NEEDS WORK** (Complex - depends on examples)

**Status:** Relevant enhancement, but depends on having more examples first

**Description:**
Identify common design patterns from example usage and create abstract classes or helpers to minimize boilerplate.

**Patterns to consider:**

1. **Single source, single purpose consumers**
   - Read from one stream, process, output somewhere

2. **Two source event triggers**
   - One source watches for events
   - Triggers actions with the other source
   - Examples: #2 and #3

3. **Asynchronous vs synchronous**
   - Threading-based (current approach)
   - Async/await patterns
   - Synchronous blocking patterns

**Recommendation:**
1. First create more examples (issues #1, #2, #3)
2. Identify repeated patterns in those examples
3. Extract common abstractions
4. Create helper classes or decorators

**Possible abstractions:**
```python
class BufferConsumer(ABC):
    """Base class for consuming from a BufferReader"""

class EventTriggeredConsumer(BufferConsumer):
    """Watches one source, triggers actions on events"""

class MultiSourceConsumer(BufferConsumer):
    """Coordinates multiple BufferReaders"""
```

**Effort:** Complex (requires examples first to identify patterns)

**Dependencies:** Should be done after creating more example applications

**Related:** Issues #1, #2, #3

---

## Summary of Recommendations

**Close immediately:**
- #4 (moved to videostream2py)
- #20 (already implemented)

**Simple fixes - next PR:**
- #10 (BufferReader.__next__ compatibility)
- #18 (check if reader started)
- #8 (add timeout parameter - builds on existing blocking)

**Medium effort - near term:**
- #17 (revise BufferReader - address TODOs)
- #14 (slicing joinable data)
- #15 (custom exceptions)
- #13 (notebook compatibility)

**Examples/applications:**
- #2 (tag sound events)
- #3 (record as you type)

**Ongoing/long-term:**
- #1 (usage examples - continue incrementally)
- #11 (various sources - continue with plugin packages)
- #5 (generalize consumers - after more examples exist)

**Needs investigation:**
- #9 (clarify what's being skipped)
- #16 (review wiki notes)
