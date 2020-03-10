from typing import Any, Optional

import cv2
import operator

from stream2py import SourceReader
from stream2py.utility.typing_hints import ComparableType

_ITEMGETTER_0 = operator.itemgetter(0)


class VideoCapture(SourceReader):
    """Video Capture using OpenCV"""

    def __init__(self, video_input=0):
        """
        https://docs.opencv.org/4.2.0/d8/dfe/classcv_1_1VideoCapture.html#ac4107fb146a762454a8a87715d9b7c96
        https://docs.opencv.org/4.2.0/d8/dfe/classcv_1_1VideoCapture.html#aabce0d83aa0da9af802455e8cf5fd181

        :param video_input: filename or device id, see cv2.VideoCapture documentation for more info
        """
        self.video_capture = None
        self._bt = -1
        self.video_input = video_input

    def open(self) -> None:
        self._bt = self.get_timestamp()
        self.video_capture = cv2.VideoCapture(self.video_input)
        if self.is_opened() is False:
            raise IOError(f"{self.__class__.__name__} error opening video stream or file: {self.video_input}")

    def read(self) -> Optional[Any]:
        ret, frame = self.video_capture.read()
        return self.get_timestamp(), ret, frame

    def close(self) -> None:
        self.video_capture.release()

    @property
    def info(self) -> dict:
        _info = {'video_input': self.video_input, 'bt': self._bt}
        if self.is_opened():
            _info.update(frame_width=int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                         frame_height=int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                         fps=self.video_capture.get(cv2.CAP_PROP_FPS))
        return _info

    def key(self, data) -> ComparableType:
        """
        :param data: (timestamp, ret, frame)
        :return: timestamp
        """
        return _ITEMGETTER_0(data)

    def is_opened(self) -> bool:
        return self.video_capture is not None and self.video_capture.isOpened()


if __name__ == "__main__":

    with VideoCapture(video_input=0) as cap:
        print(cap.info)
        print("Press 'q' to quit")
        while cap.is_opened():
            ts, ret, frame = cap.read()
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
