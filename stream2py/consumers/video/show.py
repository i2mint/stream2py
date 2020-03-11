from contextlib import suppress
import cv2
import threading

from stream2py import BufferReader
from stream2py.buffer_consumer import BufferReaderConsumer
from stream2py.utility.typing_hints import Union


class VideoShow(BufferReaderConsumer):
    def __init__(self, buffer_reader: BufferReader, interval: Union[int, float], window_name: str = 'VideoShow'):
        super().__init__(buffer_reader, interval)
        self.window_name = window_name
        self.show_event = threading.Event()

    def reader_handler(self, buffer_reader: BufferReader):
        for timestamp, ret, frame in iter(buffer_reader):
            if self.stop_event.is_set():
                break
            if self.show_event.is_set():
                cv2.imshow(self.window_name, frame)
                # TODO: cv2.waitKey seems to be required, time.sleep doesn't work
                #   Figure out how to not use waitKey
                cv2.waitKey(int(self.interval * 1000))

    def start(self):
        self.show_event.set()
        super().start()

    def stop(self):
        super().stop()
        with suppress(cv2.error):
            cv2.destroyWindow(self.window_name)
        self.show_event.clear()


if __name__ == "__main__":
    from stream2py import StreamBuffer
    from stream2py.sources.video import VideoCapture
    from stream2py.sources.keyboard_input import KeyboardInputSourceReader

    source_reader = VideoCapture(video_input=0)
    with StreamBuffer(source_reader=source_reader, maxlen=1000) as stream_buffer:
        buffer_reader = stream_buffer.mk_reader()

        with VideoShow(buffer_reader=buffer_reader, interval=0.001, window_name="show_demo") as show:
            with StreamBuffer(KeyboardInputSourceReader(), maxlen=100) as key:
                for idx, ts, char in iter(key):
                    print(f"char={char}", end='\n\r')
                    if char == 'q':
                        print('quitting', end='\n\r')
                        break
                    elif char == 'p':
                        print('pause video display', end='\n\r')
                        show.show_event.clear()
                    elif char == 's':
                        print('start video display', end='\n\r')
                        show.show_event.set()
