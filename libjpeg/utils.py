import enum
from math import ceil
import os
from pathlib import Path
from typing import Union, BinaryIO, Any, Dict, cast, TYPE_CHECKING
import warnings

import numpy as np

import _libjpeg


if TYPE_CHECKING:  # pragma: no cover
    from pydicom.dataset import Dataset


class Version(enum.IntEnum):
    v1 = 1
    v2 = 2


COLOURSPACE = {
    "MONOCHROME1": 0,
    "MONOCHROME2": 0,
    "RGB": 1,
    "YBR_FULL": 0,
    "YBR_FULL_422": 0,
}


LIBJPEG_ERROR_CODES = {
    -1024: "A parameter for a function was out of range",
    -1025: "Stream run out of data",
    -1026: "A code block run out of data",
    -1027: "Tried to perform an unputc or or an unget on an empty stream",
    -1028: "Some parameter run out of range",
    -1029: "The requested operation does not apply",
    -1030: "Tried to create an already existing object",
    -1031: "Tried to access a non-existing object",
    -1032: "A non-optional parameter was left out",
    -1033: "Forgot to delay a 0xFF",
    -1034: ("Internal error: the requested operation is not available"),
    -1035: (
        "Internal error: an item computed on a former pass does not "
        "coincide with the same item on a later pass"
    ),
    -1036: "The stream passed in is no valid jpeg stream",
    -1037: (
        "A unique marker turned up more than once. The input stream is "
        "most likely corrupt"
    ),
    -1038: "A misplaced marker segment was found",
    -1040: (
        "The specified parameters are valid, but are not supported by "
        "the selected profile. Either use a higher profile, or use "
        "simpler parameters (encoder only). "
    ),
    -1041: (
        "Internal error: the worker thread that was currently active had "
        "to terminate unexpectedly"
    ),
    -1042: (
        "The encoder tried to emit a symbol for which no Huffman code "
        "was defined. This happens if the standard Huffman table is used "
        "for an alphabet for which it was not defined. The reaction "
        "to this exception should be to create a custom huffman table "
        "instead"
    ),
    -2046: "Failed to construct the JPEG object",
}


def decode(
    stream: Union[str, os.PathLike, bytes, bytearray, BinaryIO],
    colour_transform: int = 0,
    reshape: bool = True,
) -> np.ndarray:
    """Return the decoded JPEG data from `arr` as a :class:`numpy.ndarray`.

    .. versionchanged:: 1.2

        `stream` can now also be :class:`str` or :class:`pathlib.Path`

    Parameters
    ----------
    stream : str, pathlib.Path, bytes or file-like
        The path to the JPEG file or a Python object containing the
        encoded JPEG data. If using a file-like then the object must have
        ``tell()``, ``seek()`` and ``read()`` methods.
    colour_transform : int, optional
        The colour transform used, one of:
        | ``0`` : No transform applied (default)
        | ``1`` : RGB to YCbCr
        | ``2`` : JPEG-LS pseudo RCT or RCT
        | ``3`` : Freeform
    reshape : bool, optional
        Reshape and re-view the output array so it matches the image data
        (default), otherwise return a 1D array of ``np.uint8``.

    Returns
    -------
    numpy.ndarray
        An array of containing the decoded image data.

    Raises
    ------
    RuntimeError
        If the decoding failed.
    """
    if isinstance(stream, (str, Path)):
        with open(stream, "rb") as f:
            buffer = f.read()
    elif isinstance(stream, (bytes, bytearray)):
        buffer = stream
    else:
        # BinaryIO
        stream = cast(BinaryIO, stream)
        required_methods = ["read", "tell", "seek"]
        if not all([hasattr(stream, meth) for meth in required_methods]):
            raise TypeError(
                f"Invalid type '{type(stream).__name__}' - must be the path "
                "to a JPEG file, a buffer containing the JPEG data or an open "
                "JPEG file-like"
            )
        buffer = stream.read()

    status, out, params = _libjpeg.decode(buffer, colour_transform, as_array=True)
    status = status.decode("utf-8")
    code, msg = status.split("::::")
    code = int(code)

    if code == 0 and reshape:
        bpp = ceil(params["precision"] / 8)
        if bpp == 2:
            out = out.view("<u2")

        shape = [params["rows"], params["columns"]]
        if params["nr_components"] > 1:
            shape.append(params["nr_components"])

        return cast(np.ndarray, out.reshape(*shape))

    if code == 0 and not reshape:
        return cast(np.ndarray, out)

    if code in LIBJPEG_ERROR_CODES:
        raise RuntimeError(
            f"libjpeg error code '{code}' returned from Decode(): "
            f"{LIBJPEG_ERROR_CODES[code]} - {msg}"
        )

    raise RuntimeError(f"Unknown error code '{code}' returned from Decode(): {msg}")


def decode_pixel_data(
    src: bytes,
    ds: Union["Dataset", Dict[str, Any], None] = None,
    version: int = Version.v1,
    **kwargs: Any,
) -> Union[np.ndarray, bytearray]:
    """Return the decoded JPEG data from `arr` as a :class:`numpy.ndarray`.

    Intended for use with *pydicom* ``Dataset`` objects.

    Parameters
    ----------
    src : bytes
        A Python :class:`bytes` instance containing the encoded JPEG data.
    ds : pydicom.dataset.Dataset, optional
        A :class:`~pydicom.dataset.Dataset` containing the group ``0x0028``
        elements corresponding to the *Pixel Data*. Must contain a
        (0028,0004) *Photometric Interpretation* element with the colour
        space of the pixel data, one of ``'MONOCHROME1'``, ``'MONOCHROME2'``,
        ``'RGB'``, ``'YBR_FULL'``, ``'YBR_FULL_422'``.
    version : int, optional

        * If ``1`` (default) then return the image data as an :class:`numpy.ndarray`
        * If ``2`` then return the image data as :class:`bytearray`

    Returns
    -------
    bytearray | numpy.ndarray
        The image data as either a bytearray or ndarray.

    Raises
    ------
    RuntimeError
        If the decoding failed.
    """
    ds = {} if not ds else ds

    if version == Version.v1:
        photometric_interpretation = kwargs.get("photometric_interpretation")
        pi = ds.get("PhotometricInterpretation", photometric_interpretation)
        if not pi:
            raise ValueError(
                "The (0028,0004) Photometric Interpretation element is missing "
                "from the dataset"
            )

        try:
            transform = COLOURSPACE[pi]
        except KeyError:
            warnings.warn(
                f"Unsupported (0028,0004) Photometric Interpretation '{pi}', no "
                "colour transformation will be applied"
            )
            transform = 0

        return decode(src, transform, reshape=False)

    # Version 2
    status, out, params = _libjpeg.decode(src, colourspace=0, as_array=False)
    status = status.decode("utf-8")
    code, msg = status.split("::::")
    code = int(code)

    if code == 0:
        return cast(bytearray, out)

    if code in LIBJPEG_ERROR_CODES:
        raise RuntimeError(
            f"libjpeg error code '{code}' returned from Decode(): "
            f"{LIBJPEG_ERROR_CODES[code]} - {msg}"
        )

    raise RuntimeError(f"Unknown error code '{code}' returned from Decode(): {msg}")


def get_parameters(
    stream: Union[str, os.PathLike, bytes, bytearray, BinaryIO],
) -> Dict[str, int]:
    """Return a :class:`dict` containing JPEG image parameters.

    .. versionchanged:: 1.2

        `stream` can now also be :class:`str` or :class:`pathlib.Path`

    Parameters
    ----------
    stream : str, Path, bytes
        The path to the JPEG file, a 1D array of ``np.uint8``, or a Python
        :class:`bytes` object containing the raw encoded JPEG image.

    Returns
    -------
    dict
        A :class:`dict` containing JPEG image parameters with keys including
        ``'rows'``, ``'columns'``, ``"nr_components"`` and
        ``"precision"``.

    Raises
    ------
    RuntimeError
        If reading the encoded JPEG data failed.
    """
    if isinstance(stream, (str, Path)):
        with open(stream, "rb") as f:
            buffer = f.read()
    elif isinstance(stream, (bytes, bytearray)):
        buffer = stream
    else:
        stream = cast(BinaryIO, stream)
        buffer = stream.read()

    status, params = _libjpeg.get_parameters(buffer)
    status = status.decode("utf-8")
    code, msg = status.split("::::")
    code = int(code)

    if code == 0:
        return cast(Dict[str, int], params)

    if code in LIBJPEG_ERROR_CODES:
        raise RuntimeError(
            f"libjpeg error code '{code}' returned from GetJPEGParameters(): "
            f"{LIBJPEG_ERROR_CODES[code]} - {msg}"
        )

    raise RuntimeError(
        f"Unknown error code '{code}' returned from GetJPEGParameters(): {msg}"
    )
