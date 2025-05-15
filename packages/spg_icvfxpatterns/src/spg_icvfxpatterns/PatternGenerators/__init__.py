"""
Copyright 2024 Netflix Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from spg_icvfxpatterns.PatternGenerators.alignment import Alignment as _Alignment
from spg_icvfxpatterns.PatternGenerators.bitdepth import BitDepth as _BitDepth
from spg_icvfxpatterns.PatternGenerators.checkboard import Checkerboard as _Checkerboard
from spg_icvfxpatterns.PatternGenerators.colorPatch import ColorPatch as _ColorPatch
from spg_icvfxpatterns.PatternGenerators.dataRange import DataRange as _DataRange
from spg_icvfxpatterns.PatternGenerators.exposureStops import ExposureStops as _ExposureStops
from spg_icvfxpatterns.PatternGenerators.frameCountSync import FrameCountSync as _FrameCountSync
from spg_icvfxpatterns.PatternGenerators.linearSteppedColors import LinearSteppedColors as _LinearSteppedColors
from spg_icvfxpatterns.PatternGenerators.linearSteppedRamp import LinearSteppedRamp as _LinearSteppedRamp
from spg_icvfxpatterns.PatternGenerators.movingBars import MovingBars as _MovingBars
from spg_icvfxpatterns.PatternGenerators.realBlackLevel import RealBlackLevel as _RealBlackLevel
from spg_icvfxpatterns.PatternGenerators.referenceImage import ReferenceImage as _ReferenceImage


# Registration for each of the generators written
_patterns = {
    _FrameCountSync.pattern_type: _FrameCountSync,
    _Checkerboard.pattern_type: _Checkerboard,
    _LinearSteppedRamp.pattern_type: _LinearSteppedRamp,
    _DataRange.pattern_type: _DataRange,
    _BitDepth.pattern_type: _BitDepth,
    _ColorPatch.pattern_type: _ColorPatch,
    _MovingBars.pattern_type: _MovingBars,
    _LinearSteppedColors.pattern_type: _LinearSteppedColors,
    _RealBlackLevel.pattern_type: _RealBlackLevel,
    _Alignment.pattern_type: _Alignment,
    _ReferenceImage.pattern_type: _ReferenceImage,
    _ExposureStops.pattern_type: _ExposureStops
}


def get_patterns():
    """ Returns all of the patterns which are registered within the plugin
    """
    return _patterns
