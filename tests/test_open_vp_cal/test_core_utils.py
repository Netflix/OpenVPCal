import os
import unittest

import OpenImageIO as Oiio

import open_vp_cal.imaging.imaging_utils
from open_vp_cal.core import utils
from open_vp_cal.led_wall_settings import LedWallSettings
from test_utils import TestBase


class TestConversionFunctions(TestBase):
    def test_nits_to_pq(self):
        self.assertAlmostEqual(utils.nits_to_pq(1000), 0.75182709, places=6)

    def test_pq_to_nits(self):
        self.assertAlmostEqual(utils.pq_to_nits(0.75182709), 1000, places=0)

    def test_scale_value(self):
        self.assertEqual(utils.scale_value(5, 0, 10, 0, 100), 50)

    def test_get_grey_signals(self):
        grey_signals = utils.get_grey_signals(1000, 30)
        self.assertEqual(len(grey_signals), 31)
        self.expected = [0.0, 0.00013639522724705802, 0.0006033383211292647, 0.0015714798179450899,
                         0.003266500748680244, 0.005979361165697721, 0.010082584221998288, 0.016050548996894235,
                         0.02448460250871675, 0.03614414232884348, 0.051985120426098305, 0.07320778157555699,
                         0.10131590619337878, 0.1381904054049494, 0.18618084954300218, 0.24821944400218687,
                         0.32796315553708333, 0.42997121218255524, 0.5599271485255631, 0.7249170731590064,
                         0.9337790656236824, 1.197542789328075, 1.5299838313957432, 1.9483243455105288,
                         2.474120808930801, 3.1343918215676685, 3.963054834401218, 5.002761800354198,
                         6.3072517704151005, 7.944375846163065, 10.0000000000002]

        for a, b in zip(self.expected, grey_signals):
            self.assertAlmostEqual(a, b, places=6)

    def test_oiio_to_numpy_to_oiio(self):
        folder = self.get_test_sequence_folder()
        _files = os.listdir(folder)

        first_file = _files[0]
        file_path = os.path.join(folder, first_file)

        img_buf = Oiio.ImageBuf(file_path)
        array = open_vp_cal.imaging.imaging_utils.image_buf_to_np_array(img_buf)
        new_img_buf = open_vp_cal.imaging.imaging_utils.img_buf_from_numpy_array(array)

        output_file_path = os.path.join(self.get_test_output_folder(), "test_oiio_to_numpy_to_oiio.exr")

        open_vp_cal.imaging.imaging_utils.write_image(new_img_buf, output_file_path, "half")

        self.compare_image_files(file_path, output_file_path, "exr")

    def test_topological_sort(self):
        # Create instances
        instance_a = self.project_settings.add_led_wall("A")
        instance_b = self.project_settings.add_led_wall("B")
        instance_c = self.project_settings.add_led_wall("C")
        instance_d = self.project_settings.add_led_wall("D")
        instance_e = self.project_settings.add_led_wall("E")

        instance_b.reference_wall = instance_a
        instance_c.reference_wall = instance_b
        instance_e.reference_wall = instance_d

        led_walls = [instance_c, instance_e, instance_d, instance_b, instance_c, instance_a]

        # Get sorted instances
        sorted_instances = utils.led_wall_reference_wall_sort(led_walls)
        sorted_names = [instance.name for instance in sorted_instances]

        self.assertEqual(sorted_names, ["A", "B", "C", "D", "E"])

    def test_legal_extended(self):
        expected_minimum_legal = 0.06256109481915934
        expected_maximum_legal = 0.7442303056833649
        expected_minimum_extended = 0
        expected_maximum_extended = 1.0

        minimum_legal, maximum_legal, minimum_extended, maximum_extended = utils.get_legal_and_extended_values(
            1500
        )

        self.assertEqual(expected_minimum_legal, minimum_legal)
        self.assertEqual(expected_maximum_legal, maximum_legal)
        self.assertEqual(expected_minimum_extended, minimum_extended)
        self.assertEqual(expected_maximum_extended, maximum_extended)



