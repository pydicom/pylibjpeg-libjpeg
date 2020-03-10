"""Set package shortcuts."""

import sys

from ._config import DICOM_ENCODERS, DICOM_DECODERS
from ._version import __version__
from .utils import decode, decode_pixel_data, get_parameters


# Add the testing data to libjpeg (if available)
try:
    import data as _data
    globals()['data'] = _data
    # Add to cache - needed for pytest
    sys.modules['libjpeg.data'] = _data
except ImportError:
    pass
