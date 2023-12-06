import os
from test_open_vp_cal.test_utils import TestProcessorBase


from open_vp_cal.framework.identify_separation import SeparationResults
from open_vp_cal.framework.sample_patch import SamplePatch, SampleRampPatches
from open_vp_cal.framework.frame import Frame
from open_vp_cal.core import constants


class TestSamplePatch(TestProcessorBase):
    def setUp(self):
        super(TestSamplePatch, self).setUp()

        self.separation_results = SeparationResults()
        red_frame = Frame(self.led_wall.project_settings)
        red_frame.frame_num = 73

        green_frame = Frame(self.led_wall.project_settings)
        green_frame.frame_num = 78

        self.separation_results.first_red_frame = red_frame
        self.separation_results.first_green_frame = green_frame
        self.patch = ""
        self.expected = [[]]
        self.class_to_run = SamplePatch

    def run_samples(self):
        sample_patch = self.class_to_run(
            self.led_wall, self.separation_results, self.patch
        )
        results = sample_patch.run()
        for patch_count, result in enumerate(results):
            for frame in result.frames:
                output_folder = os.path.join(
                    self.get_test_output_folder(),
                    self.patch,
                    str(patch_count)
                )
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)

                output_path = os.path.join(output_folder, frame.file_name.replace(".exr", ".png"))
                frame.image_buf.write(
                    output_path
                )
        return results

    def check_samples(self):
        results = self.run_samples()
        for count, result in enumerate(results):
            for a, b in zip(self.expected[count], result.samples):
                self.assertAlmostEqual(a, b, places=3, msg="\nExpected: {0}\nActual: {1}".format(
                    self.expected[count], result.samples))


class TestSampleGrey18Patch(TestSamplePatch):
    def setUp(self):
        super(TestSampleGrey18Patch, self).setUp()
        self.patch = constants.PATCHES.GREY_18_PERCENT
        self.expected = [[0.1803355316321055, 0.180380309621493, 0.18036188185214996]]

    def test_samples(self):
        self.check_samples()


class TestSampleRedDesPatch(TestSamplePatch):
    def setUp(self):
        super(TestSampleRedDesPatch, self).setUp()
        self.patch = constants.PATCHES.RED_PRIMARY_DESATURATED
        self.expected = [[0.09252411375443141, 0.02227468105653922, 0.01834860195716222]]

    def test_samples(self):
        self.check_samples()


class TestSampleGreenDesPatch(TestSamplePatch):
    def setUp(self):
        super(TestSampleGreenDesPatch, self).setUp()
        self.patch = constants.PATCHES.GREEN_PRIMARY_DESATURATED
        self.expected = [[0.04665279636780421, 0.12675440311431885, 0.016375088443358738]]

    def test_samples(self):
        self.check_samples()


class TestSampleBlueDesPatch(TestSamplePatch):
    def setUp(self):
        super(TestSampleBlueDesPatch, self).setUp()
        self.patch = constants.PATCHES.BLUE_PRIMARY_DESATURATED
        self.expected = [[0.02915329299867153, 0.021691843246420223, 0.12850590546925864]]

    def test_samples(self):
        self.check_samples()


class TestSampleRampPatches(TestSamplePatch):
    def setUp(self):
        super(TestSampleRampPatches, self).setUp()
        self.patch = constants.PATCHES.EOTF_RAMPS
        self.class_to_run = SampleRampPatches
        self.expected = [
            [-0.00023599637885733196, -1.7293414733406582e-05, -0.00041239183822957176],
            [-0.00022264069896967462, -1.0237189599138219e-05, -0.00039078151651968557],
            [-0.00024125237541738898, -2.1769198004525e-05, -0.00041594818079223234],
            [-0.00024870016689722735, -2.5220238815866953e-05, -0.0004180626807889591],
            [-0.0002430518507026136, -1.9848392488105066e-05, -0.0004077810056818028],
            [-0.00012086906887513275, 0.00010241770845217009, -0.0002917163268042107],
            [4.2464268820670746e-05, 0.00025050600136940676, -0.00013119383462859938],
            [0.00035190955774548155, 0.0005530322475048403, 0.00017146689060609788],
            [0.0008287379168905318, 0.0010187186999246478, 0.0006381718364233772],
            [0.001656813236574332, 0.00186426662063847, 0.0014366924297064543],
            [0.002733138855546713, 0.0029535592378427586, 0.002473267105718454],
            [0.004275312026341756, 0.004547247352699439, 0.00391930527985096],
            [0.006786731692651908, 0.0071651809848845005, 0.006376212928444147],
            [0.00978938303887844, 0.010250053678949675, 0.009441771234075228],
            [0.013981721984843412, 0.01435073558241129, 0.013549923586348692],
            [0.02069494128227234, 0.02097059537967046, 0.019918183485666912],
            [0.028137420614560444, 0.028515731915831566, 0.02733102875451247],
            [0.04012227182586988, 0.04060416668653488, 0.0389863687256972],
            [0.05330203970273336, 0.05406687408685684, 0.05209167798360189],
            [0.06791794796784718, 0.06853647778431575, 0.06665374090274175],
            [0.09022967020670573, 0.09061562021573384, 0.08905454476674397],
            [0.11509217321872711, 0.11539770662784576, 0.11404069016377132],
            [0.15313838422298431, 0.15327356259028116, 0.15247641007105509],
            [0.1957181046406428, 0.1956292192141215, 0.19593645135561624],
            [0.24995515743891397, 0.2498891701300939, 0.25099965929985046],
            [0.33329776922861737, 0.33191150426864624, 0.33672898014386493],
            [0.4258450170358022, 0.4187030792236328, 0.43527812759081524],
            [0.5499520500500997, 0.5376289486885071, 0.5629170934359232],
            [0.7426373561223348, 0.7252756754557291, 0.7479979991912842],
            [0.9440053502718607, 0.9350845615069071, 0.9536968270937601],
            [1.1342713038126628, 1.1289612452189128, 1.1495651404062908]
        ]

    def test_samples(self):
        self.check_samples()

