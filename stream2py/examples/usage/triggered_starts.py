"""
=================================
Triggered Starts in a Typing Test
=================================

.. graphviz::

    digraph components {
        subgraph cluster_0 {
            style=filled;
            color=lightgrey;
            node [style=filled,color=white];
            label="Sources";
            labeljust="l"
            "TypingTest"
            "KeyboardInput"
        }

        subgraph cluster_1 {
            node [style=filled];
            label="Readers";
            labeljust="l"
            color=lightgrey
            node [style=filled,color=lightgrey];
            "TestProctor"
            "PromptSwitch"
        }
        "KeyboardInput" -> "PromptSwitch" -> "TypingTest" -> "TestProctor";
        "KeyboardInput" -> "TestProctor";
    }

This example demonstrates the usage of stream2py with 4 asynchronous components:

1. KeyboardInputSourceReader starts at the launch of this program and listens to key presses.
2. TypingTest waits for start, stop, and add prompt commands.
3. PromptSwitch reads keyboard inputs for commands and tells TypingTest what to do.
4. TestProctor gives you TypingTest prompts and grades your keyboard input submissions.

Usage
-----
Launching the script:
::
    python -m stream2py.examples.usage.triggered_starts

.. graphviz::

    digraph flow_chart {
        label="User Flow";
        labeljust="l"
        labelloc="t"
        splines=polyline
        nodesep=.2
        {
            node [shape=oval]
            enter [label="Begin"]
            exit [label="Exit"]
        }
        {
            node [shape=diamond label="Is Started?"]
            started_start
            started_stop
            started_other
        }
        {
            node [shape=box]
            start [label="Start"]
            stop [label="Stop"]
            submit [label="Submit for Score"]
            prompt [label="New Test Prompt"]
            usage [label="Display Commands"]
        }
        input [shape=parallelogram, label="Keyboard Input"]
        enter -> usage -> input;
        input -> started_start [ headlabel=<<font color="grey25">"start"</font>>, labeldistance=2];
        input -> started_stop [ headlabel=<<font color="grey25">"stop"</font>>, labeldistance=3 ];
        input -> started_other [ headlabel=<<font color="grey25">"other"*</font>>, labeldistance=2.5 ];
        input -> exit [ headlabel=<<font color="grey25">"exit"</font>>, labeldistance=1.5 ];
        started_start -> submit  [ label="Yes" ];
        started_start -> start [ label="No" ];
        started_stop -> stop [ label="Yes" ];
        started_stop -> usage [ label="No" ];
        started_other -> submit [ label="Yes" ];
        started_other -> usage [ label="No" ];
        submit -> prompt -> input;
        start -> prompt
        stop -> input
    }

Classes
-------

.. autoclass:: stream2py.sources.keyboard_input.KeyboardInputSourceReader
.. autoclass:: TypingTest
.. autoclass:: PromptSwitch
.. autoclass:: TestProctor


.. todo::
    * Generalize event based triggers.
    * Refactor to simplify design patterns.
    * Clarify what components are doing and the objectives of the example.
"""


from collections import deque
from contextlib import contextmanager, suppress
import difflib
import operator
import threading
import time

from stream2py import SourceReader, StreamBuffer, BufferReader
from stream2py.sources.keyboard_input import KeyboardInputSourceReader
from stream2py.utility.typing_hints import (
    ComparableType,
    Any,
    Optional,
    Iterable,
    Union,
)

_ITEMGETTER_0 = operator.itemgetter(0)
_TYPING_TEST_PROMPTS = '''Welcome to the typing test tutorial!
This example demonstrates the usage of stream2py with 4 asynchronous components.
First is KeyboardInputSourceReader which starts at the launch of this program.
Second is TypingTest, also a SourceReader, which queues up test prompts when started.
Third is PromptSwitch, a BufferReader consumer that reads keyboard inputs for commands and tells TypingTest what to do.
Last is TestProctor, a BufferReader consumer that
'''.splitlines(
    keepends=False
)


class TypingTest(
    SourceReader
):  # TODO: make an abc that adds timestamp or counter automatically
    PROMPT_END = None

    def __init__(self, prompts: Iterable[str]):
        self.prompts = prompts
        self.bt = -1

        self.prompt_deque = deque(prompts)
        self.prompt_deque.append(TypingTest.PROMPT_END)

        self._release_lock = threading.Lock()
        self._release_deque = deque()

    def open(self) -> None:
        self._reset_deque_order()
        self.bt = self.get_timestamp()
        with self._release_lock:
            self._release_deque.clear()

    def read(self) -> Optional[Any]:
        if len(self._release_deque) > 0:
            with self._release_lock:
                return self._release_deque.popleft()

    def close(self) -> None:
        pass

    @property
    def info(self) -> dict:
        return {'bt': self.bt, 'prompts': self.prompts}

    def key(self, data: Any) -> ComparableType:
        return _ITEMGETTER_0(data)

    def add_prompt(self):
        with self._release_lock:
            prompt = self.prompt_deque[0]
            timestamp = self.get_timestamp()
            self._release_deque.append((timestamp, prompt))
        self.prompt_deque.rotate(-1)
        return prompt

    def _reset_deque_order(self):
        while self.prompt_deque[-1] is not TypingTest.PROMPT_END:
            self.prompt_deque.rotate(1)


class PromptSwitch(threading.Thread):
    """PromptSwitch will recognize 3 commands: "start", "stop", and "exit" followed by a return key press.

    1. "start" will start adding prompts after each return key press.
    2. "stop" will stop adding prompts
    3. "exit" will exit the program"""

    def __init__(self, input: StreamBuffer, prompts: StreamBuffer):
        if not isinstance(input.source_reader, KeyboardInputSourceReader):
            raise TypeError(
                f'input must be a StreamBuffer with KeyboardInputSourceReader: {input}'
            )
        if not isinstance(prompts.source_reader, TypingTest):
            raise TypeError(
                f'prompts must be a StreamBuffer with TypingTest: {prompts}'
            )
        threading.Thread.__init__(self, daemon=True)
        self.stop_event = threading.Event()

        self.input = input
        self.prompts = prompts

        self.is_started = False

    def stop(self):
        self.stop_event.set()

    def run(self):
        self.display_usage()
        input_reader = self.input.mk_reader()
        for index, timestamp, char in iter(input_reader):
            if self.stop_event.is_set():
                break
            print(
                char, sep='', end='\n' if char == '\r' else '', flush=True
            )  # print input character

            if char == '\r':  # "return" key
                if self._check_trigger_string('exit', input_reader, index):
                    self.stop()
                    break
                elif self.is_started is False:
                    if self._check_trigger_string('start', input_reader, index):
                        self.prompts.start()
                        self.prompts.source_reader.add_prompt()
                        self.is_started = True
                    else:
                        self.display_usage()
                elif self._check_trigger_string('stop', input_reader, index):
                    self.prompts.stop()
                    self.is_started = False
                else:
                    prompt = self.prompts.source_reader.add_prompt()
                    if prompt is TypingTest.PROMPT_END:
                        self.prompts.stop()
                        self.is_started = False
        print('Thanks for playing!')

    @staticmethod
    def display_usage():
        print(
            'Commands that can be entered anytime:\n\r'
            ' start - begin typing test\n\r'
            ' stop  - end typing test\n\r'
            ' exit  - close program\n\r'
        )

    @staticmethod
    def _check_trigger_string(
        trigger_string: str, input_reader: BufferReader, return_index: int
    ):
        start_index = return_index - len(trigger_string)
        stop_index = return_index - 1
        input_data = input_reader.range(start=start_index, stop=stop_index, peek=True)
        input_str = ''.join(c for i, t, c in input_data)
        return input_str == trigger_string


class TestProctor(threading.Thread):
    """Give prompts and grade input"""

    def __init__(self, input: StreamBuffer, prompts: StreamBuffer):
        if not isinstance(input.source_reader, KeyboardInputSourceReader):
            raise TypeError(
                f'input must be a StreamBuffer with KeyboardInputSourceReader: {input}'
            )
        if not isinstance(prompts.source_reader, TypingTest):
            raise TypeError(
                f'prompts must be a StreamBuffer with TypingTest: {prompts}'
            )
        threading.Thread.__init__(self, daemon=True)
        self.stop_event = threading.Event()

        self.input = input
        self.prompts = prompts

    def stop(self):
        self.stop_event.set()

    def run(self):
        while not self.stop_event.is_set():
            if not self.prompts.is_running:
                time.sleep(0.1)
            else:
                prev_timestamp = None
                prev_prompt = None
                for timestamp, prompt in iter(self.prompts):
                    if prev_timestamp:
                        self.grade(prev_prompt, prev_timestamp, timestamp)
                    print('Prompt: ', prompt, sep='', end='\n\r Input: ')
                    prev_timestamp = timestamp
                    prev_prompt = prompt
                else:
                    if prev_timestamp and prev_prompt is not TypingTest.PROMPT_END:
                        self.grade(prev_prompt, prev_timestamp, float('inf'))

    def grade(
        self,
        prompt: str,
        begin_time: Union[int, float],
        end_time: Union[int, float],
        debug=False,
    ):
        input_reader = self.input.mk_reader()
        all_input_data = input_reader.range(0, float('inf'))
        relevant_characters = [
            c for i, t, c in all_input_data if begin_time <= t <= end_time
        ]
        try:
            stop_index = relevant_characters.index('\r')
        except ValueError:
            stop_index = len(relevant_characters)
        relevant_timestamps = [
            t for i, t, c in all_input_data if begin_time <= t <= end_time
        ]
        true_start_time = relevant_timestamps[0]
        true_end_time = relevant_timestamps[stop_index]
        input_string = ''.join(relevant_characters[0:stop_index])
        score = len(prompt) - sum(
            1
            for diff in difflib.ndiff(prompt, input_string)
            if not diff.startswith(' ')
        )
        time_seconds = (true_end_time - true_start_time) / 1e6
        if debug:
            print(
                f'\n\rPrompt: {prompt}\n\r'
                f' Input: {input_string}\n\r'
                f'''Characters: [{', '.join(f'"{ch}"' for ch in input_string)}]\n\r''',
                flush=True,
            )
        print(
            f'You scored {score} out of {len(prompt)} in {round(time_seconds, 1)} seconds!\n\r'
        )


@contextmanager
def source_runner(sources: dict):
    """contextmanager for putting SourceReaders in StreamBuffers and calling start and stop"""
    stream_buffers = {}
    try:
        for name, s in sources.items():
            if not isinstance(s['source'], SourceReader):
                raise TypeError(f'Source must be a SourceReader: {s}')
            stream_buffers[name] = StreamBuffer(
                source_reader=s['source'], maxlen=s['maxlen']
            )
            if s['start'] is True:
                stream_buffers[name].start()
        yield stream_buffers
    finally:
        for name, s_buf in stream_buffers.items():
            with suppress(Exception):
                s_buf.stop()


@contextmanager
def consumer_runner(consumers: dict):
    """contextmanager for calling start and stop on consumers"""
    try:
        for name, c in consumers.items():
            c.start()
        yield consumers
    finally:
        for name, c in consumers.items():
            with suppress(Exception):
                c.stop()


def main():
    sources = {
        'input': dict(source=KeyboardInputSourceReader(), start=True, maxlen=None),
        'prompts': dict(
            source=TypingTest(prompts=_TYPING_TEST_PROMPTS), start=False, maxlen=None,
        ),
    }
    with source_runner(sources) as stream_buffers:
        consumers = {
            'switch': PromptSwitch(
                input=stream_buffers['input'], prompts=stream_buffers['prompts'],
            ),
            'grader': TestProctor(
                input=stream_buffers['input'], prompts=stream_buffers['prompts'],
            ),
        }
        with consumer_runner(consumers):
            consumers['switch'].join()  # wait for PromptSwitch to exit


if __name__ == '__main__':
    main()
