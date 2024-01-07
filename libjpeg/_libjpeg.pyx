# cython: language_level=3
# distutils: language=c++

from math import ceil
from typing import Union, Dict, Tuple

from libcpp cimport bool
from libcpp.string cimport string

import numpy as np
cimport numpy as np


cdef extern from "decode.hpp":
    cdef string Decode(
        char *inArray,
        char *outArray,
        int inLength,
        int outLength,
        int colourspace,
    )

    cdef struct JPEGParameters:
        int marker
        long columns
        long rows
        int samples_per_pixel
        char bits_per_sample

    cdef string GetJPEGParameters(
        char *inArray,
        int inLength,
        JPEGParameters *param,
    )


def decode(
    src: bytes,
    colourspace: int,
    as_array: bool = False,
) -> Tuple[bytes, Union[bytes, np.ndarray, None], Dict[str, int]]:
    """Return the decoded JPEG data from `input_buffer`.

    Parameters
    ----------
    input_buffer : numpy.ndarray
        A 1D array of ``np.uint8`` containing the raw encoded JPEG image.
    colourspace : int
        | ``0`` : ``JPGFLAG_MATRIX_COLORTRANSFORMATION_NONE``
        | ``1`` : ``JPGFLAG_MATRIX_COLORTRANSFORMATION_YCBCR``
        | ``2`` : ``JPGFLAG_MATRIX_COLORTRANSFORMATION_LSRCT``
        | ``2`` : ``JPGFLAG_MATRIX_COLORTRANSFORMATION_RCT``
        | ``3`` : ``JPGFLAG_MATRIX_COLORTRANSFORMATION_FREEFORM``
    as_array : bool, optional
        If ``True`` then return the decoded image data as an ndarray, otherwise
        (default) return the decoded image data as :class:`bytearray`.

    Returns
    -------
    tuple[bytes, bytes | numpy.ndarray | None, dict]

        * The status and any error message of the decoding operation.
        * The decoded image data (if any) as either bytearray or ndarray
        * A :class:`dict` containing the image parameters
    """
    # Get the image parameters
    status, param = get_parameters(src)
    code, msg = status.decode("utf-8").split("::::")
    if int(code) != 0:
        return status, None, param

    # Pointer to first element in input array
    cdef char* p_in = <char*>src

    # Create array for output and get pointer to first element
    bpp = ceil(param['precision'] / 8)
    nr_bytes = (
        param['rows'] * param['columns'] * param['nr_components'] * bpp
    )

    cdef char *p_out
    if as_array:
        out = np.zeros(nr_bytes, dtype=np.uint8)
        p_out = <char *>np.PyArray_DATA(out)
    else:
        out = bytearray(nr_bytes)
        p_out = <char *>out

    # Decode the data - output is written to output_buffer
    status = Decode(
        p_in,
        p_out,
        len(src),
        nr_bytes,
        colourspace,
    )

    return status, out, param


def get_parameters(src: bytes) -> Tuple[int, Dict[str, int]]:
    """Return a :class:`dict` containing the JPEG image parameters.

    Parameters
    ----------
    src : bytes
        The encoded JPEG image.

    Returns
    -------
    dict
        A :class:`dict` containing the JPEG image parameters.
    """
    cdef JPEGParameters param
    param.columns = 0
    param.rows = 0
    param.samples_per_pixel = 0
    param.bits_per_sample = 0

    # Pointer to the JPEGParameters object
    cdef JPEGParameters *pParam = &param

    # Pointer to first element in input array
    cdef char* p_in = <char*>src

    # Decode the data - output is written to output_buffer
    status = GetJPEGParameters(p_in, len(src), pParam)
    parameters = {
        'rows' : param.rows,
        'columns' : param.columns,
        'nr_components' : param.samples_per_pixel,
        'precision' : param.bits_per_sample,
    }

    return status, parameters
