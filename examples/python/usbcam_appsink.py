#!/usr/bin/python3

# import cv2
import gi
import numpy as np

gi.require_version('Gst', '1.0')
from gi.repository import Gst


class GstVideo():
    """Logitech C920 USB Cam to Appsink example
    Attributes:
        devnum (int): the number of the v4l2 video device. (0 for /dev/video0, etc)
    """

    def __init__(self, devnum=0):
        """Summary
        Args:
            devnum (int): the number of the v4l2 video device. (0 for /dev/video0, etc)
        """

        Gst.init(None)

        self.devnum = devnum
        self._frame = None

        # video source element
        video_source = f'v4l2src device=/dev/video{self.devnum}'
        
        # input video capabilities choice
        # choose a combo from the v4l2-ctl --list-formats-ext output for your cmaera
        input_caps = '! video/x-raw, width=1280, height=720, format=(string)YUY2, framerate=(fraction)10/1 '

        # video convert to desired raw frame video format (RGB in this case)
        videoconv = '! videoconvert ! video/x-raw, format=(string)RGB ! videoconvert'
        
        # appsink config
        appsink_config = '! appsink emit-signals=true sync=false max-buffers=2 drop=true'
                
        # appsink empty for now
        self.video_sink = None

        # video pipeline class variable
        self.video_pipe = None
        
        # assemble pipeline list (connected to appsink at end)
        pipeline_list = [video_source, input_caps, videoconv, appsink_config]
        self.run(pipeline_list)

    def start_gst(self, config=None):
        """ Start gstreamer pipeline and sink
        Pipeline description list e.g:
            [
                'videotestsrc ! decodebin', \
                '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
                '! appsink'
            ]
        Args:
            config (list, optional): Gstreamer pileline description list
        """

        if not config:
            config = \
                [
                    'videotestsrc ! decodebin',
                    '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
                    '! appsink'
                ]

        command = ' '.join(config)
        print(f'gst pipeline: {command}')
        self.video_pipe = Gst.parse_launch(command)
        self.video_pipe.set_state(Gst.State.PLAYING)
        self.video_sink = self.video_pipe.get_by_name('appsink0')

    @staticmethod
    def gst_to_opencv(sample):
        """Transform byte array into np array
        Args:
            sample (TYPE): Description
        Returns:
            TYPE: Description
        """
        buf = sample.get_buffer()
        caps = sample.get_caps()
        array = np.ndarray(
            (
                caps.get_structure(0).get_value('height'),
                caps.get_structure(0).get_value('width'),
                3
            ),
            buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
        return array

    def frame(self):
        """ Get Frame
        Returns:
            iterable: bool and image frame, cap.read() output
        """
        return self._frame

    def frame_available(self):
        """Check if frame is available
        Returns:
            bool: true if frame is available
        """
        return type(self._frame) != type(None)

    def run(self, pipeline_list=None):
        """ Get frame to update _frame
         Args:
            pipeline_list (list, optional): Gstreamer pileline description list
        """

        self.start_gst(pipeline_list)
        # self.start_gst(
        #     [
        #         self.video_source,
        #         self.video_codec,
        #         self.video_decode,
        #         self.video_sink_conf
        #     ])

        self.video_sink.connect('new-sample', self.callback)

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        new_frame = self.gst_to_opencv(sample)
        self._frame = new_frame

        return Gst.FlowReturn.OK


if __name__ == '__main__':
    # Create the GstVideo object
    # Add devnum= if is necessary to use a different one
    video = GstVideo()

    while True:
        # Wait for the next frame
        if not video.frame_available():
            continue

        # already converted by class from gst buffer to numpy array in callback
        frame = video.frame()
        
        ## do stuff here... example opencv show frame
        print(frame.shape)
        # cv2.imshow('frame', frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break