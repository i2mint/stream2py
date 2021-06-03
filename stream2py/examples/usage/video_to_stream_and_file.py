"""
TODO:
    Maybe for next more advanced version:
    * default output files to ~/odir
    * set StreamBuffer maxlen to something reasonable
    * set VideoShow intervals based on frame_rate
    * add a lookup for VideoCapture info like frame_size and frame_rate for any give input
    * playback/recording controls
        [x] default just plays and records everything
        [ ] frame rate control
        [ ] skip back/ahead
        [ ] start/stop record based on what is currently displayed
            * need to sync VideoWriter and VideoShow
    What interface do I need for VideoWriter and VideoShow
    see how to handle syncing buffer_readers between two consumers
      sharing one buffer_reader won't work like anything expected or intended or desired
"""


from stream2py import StreamBuffer
from stream2py.sources.video import VideoCapture
from stream2py.sources.keyboard_input import KeyboardInputSourceReader
from stream2py.consumers.video.write import VideoWriter
from stream2py.consumers.video.show import VideoShow


def video_display_and_save(video_input, file_name='VideoWriter.avi', fourcc='MJPG'):
    """Display recording on screen and save to file

    TODO: fps info from devices (camera) is not accurate and need to be calculated

    :param video_input: file name or device id of video source
    :param file_name: video file path to save recording
    :param fourcc: video file encoding
    """
    source_reader = VideoCapture(video_input=video_input)
    with StreamBuffer(source_reader=source_reader, maxlen=1000) as stream_buffer:

        buffer_reader_for_write = stream_buffer.mk_reader()
        frame_size = (
            buffer_reader_for_write.source_reader_info['frame_width'],
            buffer_reader_for_write.source_reader_info['frame_height'],
        )
        fps = buffer_reader_for_write.source_reader_info['fps']

        with VideoWriter(
            buffer_reader=buffer_reader_for_write,
            interval=0.001,
            file_name=file_name,
            fourcc=fourcc,
            fps=fps,
            frame_size=frame_size,
        ) as writer:

            buffer_reader_for_show = stream_buffer.mk_reader()

            with VideoShow(
                buffer_reader=buffer_reader_for_show,
                interval=0.001,
                window_name='show_demo',
            ) as show:
                print('press "q" to end recording')
                with KeyboardInputSourceReader() as key_input:
                    for index, timestamp, char in iter(key_input):
                        if char == 'q':
                            print('quitting')
                            break


if __name__ == '__main__':
    video_display_and_save(video_input=0)
