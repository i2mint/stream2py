"""
Listen to key input
Enter a keyword to start/stop typing test

Source readers:
1. Keyboard input
    * starts with the app
2. Typing test
    * add prompt function
    * test prompt strings should describe how the app works

Consumers
1. Listen to Keyboard input to trigger typing test
    * start and stop keywords
        * basically an on off switch to listen for prompt requests
    * 'enter' to request new prompt
2. Listen to Typing test and Keyboard input and display an accuracy and time score


Add flow chart describing what is happening

"""
from collections import deque
from contextlib import contextmanager, suppress
import difflib
import operator
import threading
import time

from stream2py import SourceReader, StreamBuffer, BufferReader
from stream2py.sources.keyboard_input import KeyboardInputSourceReader
from stream2py.utility.typing_hints import ComparableType, Any, Optional, Iterable

_ITEMGETTER_0 = operator.itemgetter(0)


class TypingTest(SourceReader):  # TODO: make an abc that adds timestamp or counter automatically
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
        return {"bt": self.bt, "prompts": self.prompts}

    def key(self, data: Any) -> ComparableType:
        return _ITEMGETTER_0(data)

    def add_prompt(self):
        # TODO: handle PROMPT_END
        with self._release_lock:
            self._release_deque.append((self.get_timestamp(), self.prompt_deque[0]))
        self.prompt_deque.rotate(-1)

    def _reset_deque_order(self):
        while self.prompt_deque[-1] is not TypingTest.PROMPT_END:
            self.prompt_deque.rotate(1)


class PromptSwitch(threading.Thread):
    """PromptSwitch will recognize 3 commands: "start", "stop", and "exit" followed by a return key press.
    "start" will start adding prompts after each return key press.
    "stop" will stop adding prompts
    "exit" will exit the program"""
    def __init__(self, input: StreamBuffer, prompts: StreamBuffer):
        if not isinstance(input.source_reader, KeyboardInputSourceReader):
            raise TypeError(f"input must be a StreamBuffer with KeyboardInputSourceReader: {input}")
        if not isinstance(prompts.source_reader, TypingTest):
            raise TypeError(f"prompts must be a StreamBuffer with TypingTest: {prompts}")
        threading.Thread.__init__(self, daemon=True)
        self.stop_event = threading.Event()

        self.input = input
        self.prompts = prompts

        self.is_started = False

    def stop(self):
        self.stop_event.set()

    def run(self):
        input_reader = self.input.mk_reader()
        for index, timestamp, char in iter(input_reader):
            if self.stop_event.is_set():
                break
            print(char, sep='', end='\n' if char == '\r' else '', flush=True)

            if char == '\r':  # "return" key
                if self._check_trigger_string('exit', input_reader, index):
                    self.stop()
                    break
                elif self.is_started is False:
                    if self._check_trigger_string('start', input_reader, index):
                        self.prompts.start()
                        self.prompts.source_reader.add_prompt()
                        self.is_started = True
                elif self._check_trigger_string('stop', input_reader, index):
                    self.prompts.stop()
                    self.is_started = False
                else:
                    self.prompts.source_reader.add_prompt()

    @staticmethod
    def _check_trigger_string(trigger_string: str, input_reader: BufferReader, return_index: int):
        start_index = return_index - len(trigger_string)
        stop_index = return_index - 1
        input_data = input_reader.range(start=start_index, stop=stop_index, peek=True)
        input_str = ''.join(c for i, t, c in input_data)
        return input_str == trigger_string


class PromptGrader(threading.Thread):
    """Give prompts and grade input"""
    def __init__(self, input: StreamBuffer, prompts: StreamBuffer):
        if not isinstance(input.source_reader, KeyboardInputSourceReader):
            raise TypeError(f"input must be a StreamBuffer with KeyboardInputSourceReader: {input}")
        if not isinstance(prompts.source_reader, TypingTest):
            raise TypeError(f"prompts must be a StreamBuffer with TypingTest: {prompts}")
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
                prompts_reader = self.prompts.mk_reader()
                prev_timestamp = None
                prev_prompt = None
                for timestamp, prompt in iter(prompts_reader):
                    if prev_timestamp:
                        self.grade(prev_prompt, prev_timestamp, timestamp)
                    print(prompt, end='\n\r')
                    prev_timestamp = timestamp
                    prev_prompt = prompt
                else:
                    if prev_timestamp:
                        self.grade(prev_prompt, prev_timestamp, float('inf'))

    def grade(self, prompt, begin_time, end_time):
        input_reader = self.input.mk_reader()
        all_input_data = input_reader.range(0, float('inf'))
        begin_time = begin_time
        relevant_characters = [c for i, t, c in all_input_data if begin_time <= t <= end_time]
        try:
            stop_index = relevant_characters.index("\r")
        except ValueError:
            stop_index = len(relevant_characters)
        input_string = ''.join(relevant_characters[0:stop_index])
        score = len(prompt) - sum(1 for diff in difflib.ndiff(prompt, input_string) if not diff.startswith(" "))
        print(f"\n\rprompt={prompt}\n\r"
              f" input={input_string}\n\r"
              f" You scored {score} out of {len(prompt)}!\n\r")


def _dummy_prompt_gen(n=10):
    return (f"This is prompt number: {i}" for i in range(1, n + 1))


@contextmanager
def source_runner(sources):
    stream_buffers = {}
    try:
        for name, s in sources.items():
            if not isinstance(s['source'], SourceReader):
                raise TypeError(f"Source must be a SourceReader: {s}")
            stream_buffers[name] = StreamBuffer(source_reader=s['source'], maxlen=s['maxlen'])
            if s['start'] is True:
                stream_buffers[name].start()
        yield stream_buffers
    finally:
        for name, s_buf in stream_buffers.items():
            with suppress(Exception):
                s_buf.stop()


sources = {'input': dict(source=KeyboardInputSourceReader(), start=True, maxlen=None),
           'prompts': dict(source=TypingTest(prompts=_dummy_prompt_gen(10)), start=False, maxlen=None)}


with source_runner(sources) as stream_buffers:
    consumers = {'switch': PromptSwitch(input=stream_buffers['input'], prompts=stream_buffers['prompts']),
                 'grader': PromptGrader(input=stream_buffers['input'], prompts=stream_buffers['prompts'])}
    for name, c in consumers.items():
        c.start()

    consumers['switch'].join()  # wait for PromptSwitch to exit

    for name, c in consumers.items():
        c.stop()
