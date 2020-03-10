import cv2

from stream2py import BufferReader
from stream2py.buffer_consumer import BufferReaderConsumer
from stream2py.utility.typing_hints import Union, Optional, Tuple


class VideoWriter(BufferReaderConsumer):
    def __init__(self, buffer_reader: BufferReader, interval: Union[int, float],
                 file_name: str, fourcc: Union[str, tuple], fps: Optional[float], frame_size: Tuple[int, int]):
        """
        https://docs.opencv.org/4.2.0/dd/d9e/classcv_1_1VideoWriter.html#ac3478f6257454209fa99249cc03a5c59

        :param buffer_reader:
        :param interval:
        :param file_name:
        :param fourcc:
        :param fps:
        :param frame_size:
        """
        super().__init__(buffer_reader, interval)
        self.file_name = file_name
        self.fourcc = fourcc
        self._fourcc_int = cv2.VideoWriter_fourcc(*self.fourcc)
        self.fps = fps
        self.frame_size = frame_size
        self.video_writer = None

    def reader_handler(self, buffer_reader: BufferReader):
        for timestamp, ret, frame in iter(buffer_reader):
            if self.stop_event.is_set():
                break
            self.video_writer.write(frame)

    def start(self):
        self.video_writer = cv2.VideoWriter(self.file_name, self._fourcc_int, self.fps, self.frame_size)
        super().start()

    def stop(self):
        super().stop()
        self.video_writer.release()
        self.video_writer = None


if __name__ == "__main__":
    from stream2py import StreamBuffer
    from stream2py.sources.video import VideoCapture
    from stream2py.sources.keyboard_input import KeyboardInputSourceReader

    source_reader = VideoCapture(video_input=0)
    with StreamBuffer(source_reader=source_reader, maxlen=1000) as stream_buffer:
        buffer_reader = stream_buffer.mk_reader()
        frame_size = (buffer_reader.source_reader_info['frame_width'], buffer_reader.source_reader_info['frame_height'])
        fps = buffer_reader.source_reader_info['fps']
        with VideoWriter(buffer_reader=buffer_reader, interval=0.001, file_name="VideoWriter.avi", fourcc="MJPG",
                         fps=fps, frame_size=frame_size) as writer:
            # TODO: condition to keep open
            with StreamBuffer(KeyboardInputSourceReader(), maxlen=10) as key:
                for idx, ts, char in iter(key):
                    print(f"char={char}", end='\n\r')
                    if char == 'q':
                        print('quitting', end='\n\r')
                        break
