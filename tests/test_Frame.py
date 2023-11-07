import OpenImageIO as oiio

from open_vp_cal.framework.frame import Frame
from test_utils import TestBase


class TestFrame(TestBase):
    def setUp(self):
        """
        Method called to prepare the test fixture.
        This is called immediately before calling the test method.
        """
        super(TestFrame, self).setUp()
        self.frame = Frame(self.project_settings)
        self.frame._frame_num = 1
        self.frame._file_name = "frame_1.exr"
        self.frame._image_buf = oiio.ImageBuf()  # Create a default ImageBuf

    def test_frame_num(self):
        """
        Test the frame_num property
        """
        self.assertEqual(self.frame.frame_num, 1)

    def test_file_name(self):
        """
        Test the file_name property
        """
        self.assertEqual(self.frame.file_name, "frame_1.exr")

    def test_image_buf(self):
        """
        Test the image_buf property
        """
        self.assertIsInstance(self.frame.image_buf, oiio.ImageBuf)

    def test_str(self):
        """
        Test the __str__ method
        """
        expected_str = str({
            "frame_num": 1,
            "file_name": "frame_1.exr",
            "image_buf": str(self.frame.image_buf)
        })
        self.assertEqual(str(self.frame), expected_str)
