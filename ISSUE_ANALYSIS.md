# Issue Analysis and Resolution Plan

## Summary

This document analyzes all 17 open issues in the stream2py repository, categorizes them, identifies dependencies, and provides a resolution strategy.

## Issue Status Summary

- **Already Resolved**: 2 issues (#20, partial #8)
- **Simple Fixes**: 4 issues (#6, #10, #18, #9)
- **Medium Effort**: 4 issues (#17, #14, #15, #13)
- **Complex/Ongoing**: 4 issues (#1, #11, #5, #2, #3)
- **External/Needs Investigation**: 2 issues (#4, #16)

---

## Detailed Issue Analysis

### ✅ Already Resolved

#### Issue #20: [Add option to make BufferReader blocking to wait for future data](https://github.com/i2mint/stream2py/issues/20)
- **Status**: RESOLVED ✓
- **Category**: Feature
- **Resolution**: The `blocking` parameter already exists in `BufferReader.read()` (stream2py/buffer_reader.py:329)
- **Recommendation**: Close this issue with a comment explaining that the feature was implemented
- **Code Reference**: `buffer_reader.py:322-401`

#### Issue #8: [Add parameters (block=False, timeout=None) in BufferReader methods](https://github.com/i2mint/stream2py/issues/8)
- **Status**: PARTIALLY RESOLVED
- **Category**: Feature
- **Resolution**: The `blocking` parameter exists; `timeout` parameter is not implemented
- **Effort**: Simple (add timeout support)
- **Recommendation**: Can close or update to focus only on timeout if desired

---

### ✅ Resolved in This PR

#### Issue #6: [a `closed` parameter for SourceReader](https://github.com/i2mint/stream2py/issues/6)
- **Status**: ✓ RESOLVED in this PR
- **Category**: Feature
- **Effort**: Simple
- **Resolution**: Added `closed` property to `SourceReader` class, similar to `io.IOBase.closed`
- **Changes Made**:
  - Added `_closed` attribute to track open/close state
  - Added `closed` property that returns `self._closed`
  - Updated `__enter__` and `__exit__` to manage `_closed` flag
  - Updated `QuickSourceReader.open()` and `close()` to set flag
  - Updated docstring example to demonstrate usage
- **Code Reference**: `source_reader.py:76,129-137,165-172,244-252`

---

### 🔧 Simple Fixes (Recommended for Next Steps)

#### Issue #10: [Make BufferReader.__next__() more compatible with builtin next()](https://github.com/i2mint/stream2py/issues/10)
- **Status**: Needs review
- **Category**: Enhancement/Bug
- **Effort**: Simple
- **Description**: The `next()` function should raise `StopIteration` or yield the given default value
- **Current Behavior**: `BufferReader.__next__()` returns None while next value is unavailable
- **Expected Behavior**: Should raise `StopIteration` when iterator is exhausted, or return default if provided
- **Recommendation**: Review current implementation and adjust to match Python's iterator protocol

#### Issue #18: [What should happen if we start to read without starting the reader?](https://github.com/i2mint/stream2py/issues/18)
- **Status**: Design question
- **Category**: Enhancement/Design
- **Effort**: Simple
- **Description**: Should raise an exception if user tries to read before entering reader context
- **Recommendation**: Add a check in `BufferReader.read()` to raise a clear exception if the buffer hasn't been started
- **Related**: See wiki on [Forwarding context management](https://github.com/i2mint/stream2py/wiki/Forwarding-context-management)

#### Issue #9: [Not skipping tests and linting](https://github.com/i2mint/stream2py/issues/9)
- **Status**: Unclear what the specific issue is
- **Category**: CI/CD
- **Effort**: Simple
- **Current State**: CI configuration (.github/workflows/ci.yml) runs tests on line 43
- **Recommendation**: Need clarification on what specifically should not be skipped. Current CI runs pytest and pylint.

---

### 🛠️ Medium Effort

#### Issue #17: [Revise BufferReader](https://github.com/i2mint/stream2py/issues/17)
- **Status**: Relevant
- **Category**: Enhancement
- **Effort**: Medium
- **TODOs Identified**:
  1. `read` must get its defaults from init ✓ (already done via `_read_kwargs`)
  2. `range` must work similarly to `read` (needs review)
  3. Which init args should be keyword-only? (design decision)
  4. Consider making `read_chk_step` and `read_chk_size` (instead of just `peek`)
- **TODOs in Code**:
  - `buffer_reader.py:95` - "should `ignore_no_item_found` default be True to align with iter?"
  - `stream_buffer.py:125` - "option to auto restart source on read exception"
- **Recommendation**: Address each TODO item systematically

#### Issue #14: [Add support for slicing joinable data items](https://github.com/i2mint/stream2py/issues/14)
- **Status**: Relevant
- **Category**: Feature
- **Effort**: Medium
- **Description**: For data like waveform chunks that can be joined, `BufferReader.range()` should optionally join and trim to get exact query results
- **Recommendation**: Add optional abstract methods to `SourceReader` for joining and slicing read data items
- **Benefit**: More precise range queries for chunked data

#### Issue #15: [Review exception objects raised and figure out custom ones](https://github.com/i2mint/stream2py/issues/15)
- **Status**: Relevant
- **Category**: Enhancement
- **Effort**: Medium
- **Recommendation**: Audit all exception raising in the codebase and create custom exception classes where appropriate (e.g., `StreamNotStartedError`, `BufferOverflowError`, etc.)

#### Issue #13: [keyboard_and_audio not working in notebook](https://github.com/i2mint/stream2py/issues/13)
- **Status**: Relevant
- **Category**: Bug
- **Effort**: Medium
- **Description**: Terminal-based keyboard input (using termios) doesn't work in notebooks
- **Error**: `termios.error: (25, 'Inappropriate ioctl for device')`
- **Recommendation**: Add conditional imports and provide alternative input method for notebook environments, or document limitation

---

### 📦 Complex/Ongoing (Large Scope)

#### Issue #1: [Create usage examples and helper classes](https://github.com/i2mint/stream2py/issues/1)
- **Status**: Ongoing
- **Category**: Documentation/Examples
- **Effort**: Complex
- **Current Progress**:
  - ✓ webcam (moved to videostream2py)
  - ✓ keyboard input (moved to keyboardstream2py)
  - ✓ audio (moved to audiostream2py)
  - ⏳ url stream
  - ⏳ General saving to files
  - ⏳ Event based actions
  - ⏳ Data visualization
  - ⏳ BufferConsumer class
- **Recommendation**: Continue incremental progress; many items moved to separate plugin packages

#### Issue #11: [Various sources](https://github.com/i2mint/stream2py/issues/11)
- **Status**: Ongoing
- **Category**: Feature
- **Effort**: Complex
- **Scope**: Create SourceReaders for various sources (webcam video/audio, web-audio, keyboard, mouse, wifi packets, bluetooth, CPU/RAM usage, etc.)
- **Current Progress**: Several moved to separate packages (audiostream2py, videostream2py, keyboardstream2py, etc.)
- **Recommendation**: Continue creating SourceReaders in separate plugin packages

#### Issue #5: [Generalize StreamBuffer and BufferReader consumers](https://github.com/i2mint/stream2py/issues/5)
- **Status**: Relevant
- **Category**: Enhancement/Design
- **Effort**: Complex
- **Description**: Identify common design patterns from example usage and create abstract classes or helpers
- **Patterns to Consider**:
  1. Consumers using single source for single purpose
  2. Consumers using two sources (one watches for events, performs actions with other)
  3. Asynchronous vs synchronous patterns
- **Recommendation**: Work on this after creating more examples to identify patterns

#### Issue #2: [Tag Sound Events](https://github.com/i2mint/stream2py/issues/2)
- **Status**: Relevant (example application)
- **Category**: Example
- **Effort**: Medium-Complex
- **Description**: Create example app to annotate audio events with key presses
- **Recommendation**: Good example project for demonstrating multi-source event handling

#### Issue #3: [Two Source Event Trigger: Record as You Type](https://github.com/i2mint/stream2py/issues/3)
- **Status**: Relevant (example application)
- **Category**: Example
- **Effort**: Medium
- **Description**: Save audio recorded while typing, capturing before/after typing
- **Recommendation**: Good example demonstrating event-triggered recording

---

### 🔍 External/Needs Investigation

#### Issue #4: [New webcam SourceReader](https://github.com/i2mint/stream2py/issues/4)
- **Status**: External
- **Category**: Feature (external)
- **Resolution**: Webcam functionality moved to separate package: [videostream2py](https://github.com/i2mint/videostream2py)
- **Recommendation**: Close with comment directing to videostream2py

#### Issue #16: [Address the BufferReader(...source_reader_info...) issue](https://github.com/i2mint/stream2py/issues/16)
- **Status**: Needs investigation
- **Category**: Bug/Design
- **Reference**: [Review notes on wiki](https://github.com/i2mint/stream2py/wiki/Review-notes)
- **Effort**: Unknown (needs wiki review)
- **Recommendation**: Review wiki notes to understand the issue, then categorize

---

## Dependency Relationships

### No Strong Dependencies
Most issues are independent, but some logical groupings exist:

**Testing & Error Handling Group:**
- #10 (BufferReader.__next__() compatibility)
- #15 (Review exception objects)
- #18 (Read without starting reader)

**Enhancement Group:**
- #17 (Revise BufferReader)
- #14 (Slicing joinable data)
- #8 (Add timeout parameter)

**Examples Group:**
- #1 (Usage examples)
- #2 (Tag Sound Events)
- #3 (Record as You Type)
- #5 (Generalize consumers - depends on examples)

---

## Commit Strategy

### Commits Already Made in This PR:
1. **test: fix Python 3.11+ compatibility in test_util.py**
   - Fixed TypeError vs AttributeError for context manager protocol

2. **docs: fix syntax error in __init__.py docstring**
   - Added missing colon in property definition

3. **fix: add missing open_instance attribute to QuickSourceReader**
   - Prevents AttributeError when accessing info property

4. **fix: SimpleSourceReader should return None instead of raising StopIteration**
   - Aligns with SourceReader contract

5. **test: add comprehensive tests for blocking parameter**
   - Tests for BufferReader.read(blocking=True/False)
   - Tests for blocking behavior when buffer stops

6. **test: add comprehensive tests for QuickSourceReader**
   - Tests for basic functionality, context manager, info, key, iteration
   - Tests for custom is_valid_data filtering

7. **feat: add closed property to SourceReader (#6)**
   - Added closed property similar to io.IOBase.closed
   - Updated __enter__ and __exit__ to manage _closed flag
   - Updated QuickSourceReader to properly set closed state
   - Updated docstring with example usage

### Recommended Next Steps (Future PRs):

**Priority 1 - Quick Wins:**
- Fix #10 (BufferReader.__next__() compatibility)
- Address #18 (Read without starting reader check)
- Clarify #9 (Tests and linting)

**Priority 2 - Medium Effort:**
- Work through #17 TODOs (Revise BufferReader)
- Implement #14 (Slicing joinable data)
- Fix #13 (Notebook compatibility)
- Complete #15 (Custom exceptions)

**Priority 3 - Ongoing:**
- Continue #1 (Examples and helpers)
- Create #2 and #3 example applications
- Work on #5 after more examples exist

**Cleanup:**
- Close #20 (already implemented)
- Close #4 (moved to videostream2py)
- Investigate #16 (review wiki)

---

## Testing Strategy

### Test Coverage Improvements in This PR:
- ✅ Fixed failing test in test_util.py (Python 3.11+ compatibility)
- ✅ Added tests for blocking parameter (2 new tests)
- ✅ Added tests for QuickSourceReader (6 new tests)
- ✅ Fixed QuickSourceReader bug (missing open_instance)
- ✅ Fixed SimpleSourceReader bug (StopIteration handling)

### Test Results:
- **Before**: 11 tests (1 failing)
- **After**: 19 tests (all passing)
- **New Coverage**: BufferReader blocking behavior, QuickSourceReader functionality

---

## Documentation Improvements in This PR:

1. Fixed syntax error in `__init__.py` docstring (line 113)
2. Added documentation for `closed` property in SourceReader
3. Updated SourceReader docstring with example of closed property usage
4. Created comprehensive test files with clear docstrings

---

## Recommendations for Issue Comments

For each issue, I recommend adding a comment with:
- Current status assessment
- Whether it's resolved, in progress, or needs work
- For resolved issues: what code addresses it
- For obsolete issues: why it's no longer relevant
- For actionable issues: estimated effort and approach

---

## Conclusion

This analysis covers all 17 open issues. The work completed in this PR addresses:
- 2 bugs fixed (QuickSourceReader, SimpleSourceReader)
- 1 feature implemented (closed property, #6)
- 1 test compatibility issue fixed
- 8 new tests added
- 1 documentation error fixed

The remaining issues are categorized and prioritized for future work.
