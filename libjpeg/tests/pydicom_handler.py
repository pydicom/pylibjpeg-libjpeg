"""Handler for testing decoding of DICOM datasets.

Will eventually be obsoleted by the pylibjpeg or pydicom handler.

**Supported transfer syntaxes**

* 1.2.840.10008.1.2.4.50 : JPEG Baseline (Process 1)
* 1.2.840.10008.1.2.4.51 : JPEG Extended (Process 2 and 4)
* 1.2.840.10008.1.2.4.57 : JPEG Lossless, Non-Hierarchical (Process 14)
* 1.2.840.10008.1.2.4.70 : JPEG Lossless, Non-Hierarchical, First-Order
  Prediction (Process 14 [Selection Value 1])
* 1.2.840.10008.1.2.4.80 : JPEG-LS Lossless Image Compression
* 1.2.840.10008.1.2.4.81 : JPEG-LS Lossy (Near-Lossless) Image Compression
"""

import numpy as np
from pydicom.encaps import generate_pixel_data_frame
from pydicom.pixel_data_handlers.util import pixel_dtype, get_expected_length
from pydicom.uid import (
    JPEGBaseline,
    JPEGExtended,
    JPEGLosslessP14,
    JPEGLossless,
    JPEGLSLossless,
    JPEGLSLossy,
)

from libjpeg import decode_pixel_data


HANDLER_NAME = 'libjpeg-test'
DEPENDENCIES = {
    'numpy': ('http://www.numpy.org/', 'NumPy'),
}
SUPPORTED_TRANSFER_SYNTAXES = [
    JPEGBaseline,
    JPEGExtended,
    JPEGLosslessP14,
    JPEGLossless,
    JPEGLSLossless,
    JPEGLSLossy,
]


def is_available():
    """Return ``True`` if the handler has its dependencies met."""
    return True


def supports_transfer_syntax(tsyntax):
    """Return ``True`` if the handler supports the `tsyntax`.

    Parameters
    ----------
    tsyntax : uid.UID
        The Transfer Syntax UID of the *Pixel Data* that is to be used with
        the handler.
    """
    return tsyntax in SUPPORTED_TRANSFER_SYNTAXES


def needs_to_convert_to_RGB(ds):
    """Return ``True`` if the *Pixel Data* should to be converted from YCbCr to
    RGB.

    This affects JPEG transfer syntaxes.
    """
    return False


def should_change_PhotometricInterpretation_to_RGB(ds):
    """Return ``True`` if the *Photometric Interpretation* should be changed
    to RGB.

    This affects JPEG transfer syntaxes.
    """
    return False


def get_pixeldata(ds):
    """Return a :class:`numpy.ndarray` of the pixel data.

    Parameters
    ----------
    ds : Dataset
        The :class:`Dataset` containing an Image Pixel, Floating Point Image
        Pixel or Double Floating Point Image Pixel module and the
        *Pixel Data*, *Float Pixel Data* or *Double Float Pixel Data* to be
        converted. If (0028,0004) *Photometric Interpretation* is
        `'YBR_FULL_422'` then the pixel data will be
        resampled to 3 channel data as per Part 3, :dcm:`Annex C.7.6.3.1.2
        <part03/sect_C.7.6.3.html#sect_C.7.6.3.1.2>` of the DICOM Standard.

    Returns
    -------
    np.ndarray
        The contents of (7FE0,0010) *Pixel Data* as a 1D array.
    """
    tsyntax = ds.file_meta.TransferSyntaxUID
    # The check of transfer syntax must be first
    if tsyntax not in SUPPORTED_TRANSFER_SYNTAXES:
        raise NotImplementedError(
            "Unable to convert the pixel data as the transfer syntax "
            "is not supported by the pylibjpeg pixel data handler."
        )

    # Check required elements
    required_elements = [
        'BitsAllocated', 'Rows', 'Columns', 'PixelRepresentation',
        'SamplesPerPixel', 'PhotometricInterpretation', 'PixelData',
    ]
    missing = [elem for elem in required_elements if elem not in ds]
    if missing:
        raise AttributeError(
            "Unable to convert the pixel data as the following required "
            "elements are missing from the dataset: " + ", ".join(missing)
        )

    # Calculate the expected length of the pixel data (in bytes)
    #   Note: this does NOT include the trailing null byte for odd length data
    expected_len = get_expected_length(ds)
    if ds.PhotometricInterpretation == 'YBR_FULL_422':
        # libjpeg has already resampled the pixel data, see PS3.3 C.7.6.3.1.2
        expected_len = expected_len // 2 * 3

    p_interp = ds.PhotometricInterpretation

    # How long each frame is in bytes
    nr_frames = getattr(ds, 'NumberOfFrames', 1)
    frame_len = expected_len // nr_frames

    # The decoded data will be placed here
    arr = np.empty(expected_len, np.uint8)

    # Generators for the encoded JPG image frame(s) and insertion offsets
    generate_frames = generate_pixel_data_frame(ds.PixelData, nr_frames)
    generate_offsets = range(0, expected_len, frame_len)
    for frame, offset in zip(generate_frames, generate_offsets):
        # Encoded JPG data to be sent to the decoder
        frame = np.frombuffer(frame, np.uint8)
        arr[offset:offset + frame_len] = decode_pixel_data(
            frame, ds.group_dataset(0x0028)
        )

    return arr.view(pixel_dtype(ds))
