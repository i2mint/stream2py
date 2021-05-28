from collections import deque
from contextlib import suppress
import operator
import threading
import time
from typing import Any

from stream2py import SourceReader
from stream2py.utility.typing_hints import ComparableType


_ITEMGETTER_0 = operator.itemgetter(0)


class KeyboardInputSourceReader(SourceReader, threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self._data_lock = threading.Lock()
        self.data = deque()
        self.stop_event = threading.Event()
        self.bt = None
        self.index = 0

    def open(self):
        self.data.clear()
        self.stop_event.clear()
        self.bt = self.get_timestamp()
        self.index = 0
        self.start()

    def read(self):
        """Returns one data item

        :return: (index, timestamp, character)
        """
        if len(self.data):
            with self._data_lock:
                return self.data.popleft()

    def close(self):
        # Import getch here to avoid errors for rst preview extension when loaded within IDE terminals
        from stream2py.utility.getch import getch

        self.stop_event.set()
        getch.restore_settings()

    @property
    def info(self) -> dict:
        return {'bt': self.bt}

    def key(self, data: Any) -> ComparableType:
        """

        :param data: (index, timestamp, character)
        :return: index
        """
        return _ITEMGETTER_0(data)

    def run(self):
        # Import getch here to avoid errors for rst preview extension when loaded within IDE terminals
        from stream2py.utility.getch import getch

        try:
            while not self.stop_event.is_set():
                ch = getch.blocking()
                self.data.append(
                    (self.index, self.get_timestamp(), ch)
                )  # (index, timestamp, character)
                self.index += 1
        except Exception:
            self.close()
            raise


if __name__ == '__main__':
    with KeyboardInputSourceReader() as source:
        print('getch! Press any key! Esc to quit!')
        while True:
            data = source.read()
            if data is not None:
                index, timestamp, char = data
                print(f'{timestamp}: {char}', end='\n\r')

                if char == '\x1b':  # ESC key
                    break
