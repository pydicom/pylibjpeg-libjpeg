
import enum
from math import ceil
from pathlib import Path
import warnings

import numpy as np

import _libjpeg


LIBJPEG_ERROR_CODES = {
    -1024 : "A parameter for a function was out of range",
    -1025 : "Stream run out of data",
    -1026 : "A code block run out of data",
    -1027 : "Tried to perform an unputc or or an unget on an empty stream",
    -1028 : "Some parameter run out of range",
    -1029 : "The requested operation does not apply",
    -1030 : "Tried to create an already existing object",
    -1031 : "Tried to access a non-existing object",
    -1032 : "A non-optional parameter was left out",
    -1033 : "Forgot to delay a 0xFF",
    -1034 : (
        "Internal error: the requested operation is not available"
    ),
    -1035 : (
        "Internal error: an item computed on a former pass does not "
        "coincide with the same item on a later pass"
    ),
    -1036 : "The stream passed in is no valid jpeg stream",
    -1037 : (
        "A unique marker turned up more than once. The input stream is "
        "most likely corrupt"
    ),
    -1038 : "A misplaced marker segment was found",
    -1040 : (
        "The specified parameters are valid, but are not supported by "
        "the selected profile. Either use a higher profile, or use "
        "simpler parameters (encoder only). "
    ),
    -1041 : (
        "Internal error: the worker thread that was currently active had "
        "to terminate unexpectedly"
    ),
    -1042 : (
        "The encoder tried to emit a symbol for which no Huffman code "
        "was defined. This happens if the standard Huffman table is used "
        "for an alphabet for which it was not defined. The reaction "
        "to this exception should be to create a custom huffman table "
        "instead"
    ),
    -2046 : "Failed to construct the JPEG object",
}


def decode(stream, colour_transform=0, reshape=True):
    """Return the decoded JPEG data from `arr` as a :class:`numpy.ndarray`.

    .. versionchanged:: 1.2

        `stream` can now also be :class:`str` or :class:`pathlib.Path`

    Parameters
    ----------
    stream : str, Path, numpy.ndarray or bytes
        The path to the JPEG file, a 1D array of ``np.uint8``, or a Python
        :class:`bytes` object containing the raw encoded JPEG image.
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
            stream = f.read()

    if isinstance(stream, bytes):
        arr = np.frombuffer(stream, 'uint8')
    else:
        arr = stream

    status, out, params = _libjpeg.decode(arr, colour_transform)
    status = status.decode("utf-8")
    code, msg = status.split("::::")
    code = int(code)

    if code == 0 and reshape is True:
        bpp = ceil(params["precision"] / 8)
        if bpp == 2:
            out = out.view('uint16')

        shape = [params['rows'], params['columns']]
        if params["nr_components"] > 1:
            shape.append(params["nr_components"])

        return out.reshape(*shape)
    elif code == 0 and reshape is False:
        return out

    if code in LIBJPEG_ERROR_CODES:
        raise RuntimeError(
            "libjpeg error code '{}' returned from Decode(): {} - {}"
            .format(code, LIBJPEG_ERROR_CODES[code], msg)
        )

    raise RuntimeError(
        "Unknown error code '{}' returned from Decode(): {}"
        .format(code, msg)
    )


def decode_pixel_data(arr, ds = None, **kwargs):
    """Return the decoded JPEG data from `arr` as a :class:`numpy.ndarray`.

    Intended for use with *pydicom* ``Dataset`` objects.

    Parameters
    ----------
    arr : numpy.ndarray or bytes
        A 1D array of ``np.uint8``, or a Python :class:`bytes` object
        containing the encoded JPEG image.
    ds : pydicom.dataset.Dataset, optional
        A :class:`~pydicom.dataset.Dataset` containing the group ``0x0028``
        elements corresponding to the *Pixel Data*. Must contain a
        (0028,0004) *Photometric Interpretation* element with the colour
        space of the pixel data, one of ``'MONOCHROME1'``, ``'MONOCHROME2'``,
        ``'RGB'``, ``'YBR_FULL'``, ``'YBR_FULL_422'``.
    **kwargs

    Returns
    -------
    numpy.ndarray
        A 1D array of ``numpy.uint8`` containing the decoded image data.

    Raises
    ------
    RuntimeError
        If the decoding failed.
    """
    colours = {
        'MONOCHROME1': 0,
        'MONOCHROME2' : 0,
        'RGB' : 1,
        'YBR_FULL' : 0,
        'YBR_FULL_422' : 0,
    }

    photometric_interpretation = kwargs.get("photometric_interpretation")
    pi = ds.get("PhotometricInterpretation", photometric_interpretation)
    if not pi:
        raise ValueError(
            "The (0028,0004) Photometric Interpretation element is missing "
            "from the dataset"
        )

    try:
        transform = colours[pi]
    except KeyError:
        warnings.warn(
            f"Unsupported (0028,0004) Photometric Interpretation '{pi}', no "
            "colour transformation will be applied"
        )
        transform = 0

    return decode(arr, transform, reshape=False)


def get_parameters(stream):
    """Return a :class:`dict` containing JPEG image parameters.

    .. versionchanged:: 1.2

        `stream` can now also be :class:`str` or :class:`pathlib.Path`

    Parameters
    ----------
    stream : str, Path, numpy.ndarray or bytes
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
            stream = f.read()

    if isinstance(stream, bytes):
        arr = np.frombuffer(stream, 'uint8')
    else:
        arr = stream

    status, params = _libjpeg.get_parameters(arr)
    status = status.decode("utf-8")
    code, msg = status.split("::::")
    code = int(code)

    if code == 0:
        return params

    if code in LIBJPEG_ERROR_CODES:
        raise RuntimeError(
            "libjpeg error code '{}' returned from GetJPEGParameters(): "
            "{} - {}".format(code, LIBJPEG_ERROR_CODES[code], msg)
        )

    raise RuntimeError(
        "Unknown error code '{}' returned from GetJPEGParameters(): {}"
        .format(status, msg)
    )


def reconstruct(fin, fout, colourspace=1, falpha=None, upsample=True):
    """Simple wrapper for the libjpeg ``cmd/reconstruct::Reconstruct()``
    function.

    Parameters
    ----------
    fin : bytes
        The path to the JPEG file to be decoded.
    fout : bytes
        The path to the decoded PPM or PGM (if `falpha` is ``True``) file(s).
    colourspace : int, optional
        The colourspace transform to apply.
        | ``0`` : ``JPGFLAG_MATRIX_COLORTRANSFORMATION_NONE``  (``-c`` flag)
        | ``1`` : ``JPGFLAG_MATRIX_COLORTRANSFORMATION_YCBCR`` (default)
        | ``2`` : ``JPGFLAG_MATRIX_COLORTRANSFORMATION_LSRCT`` (``-cls`` flag)
        | ``2`` : ``JPGFLAG_MATRIX_COLORTRANSFORMATION_RCT``
        | ``3`` : ``JPGFLAG_MATRIX_COLORTRANSFORMATION_FREEFORM``
        See `here<https://github.com/thorfdbg/libjpeg/blob/87636f3b26b41b85b2fb7355c589a8c456ef808c/interface/parameters.hpp#L381>`_
        for more information.
    falpha : bytes, optional
        The path where any decoded alpha channel data will be written (as a
        PGM file), otherwise ``None`` (default) to not write alpha channel
        data. Equivalent to the ``-al file`` flag.
    upsample : bool, optional
        ``True`` (default) to disable automatic upsampling, equivalent to
        the ``-U`` flag.
    """
    if isinstance(fin, (str, Path)):
        fin = str(fin)
        fin = bytes(fin, 'utf-8')

    if isinstance(fout, (str, Path)):
        fout = str(fout)
        fout = bytes(fout, 'utf-8')

    if falpha and isinstance(falpha, (str, Path)):
        falpha = str(falpha)
        falpha = bytes(falpha, 'utf-8')

    _libjpeg.reconstruct(fin, fout, colourspace, falpha, upsample)
