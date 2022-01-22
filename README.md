[![Build Status](https://github.com/pydicom/pylibjpeg-libjpeg/workflows/unit-tests/badge.svg)](https://github.com/pydicom/pylibjpeg-libjpeg/actions?query=workflow%3Aunit-tests)
[![codecov](https://codecov.io/gh/pydicom/pylibjpeg-libjpeg/branch/master/graph/badge.svg)](https://codecov.io/gh/pydicom/pylibjpeg-libjpeg)
[![PyPI version](https://badge.fury.io/py/pylibjpeg-libjpeg.svg)](https://badge.fury.io/py/pylibjpeg-libjpeg)
[![Python versions](https://img.shields.io/pypi/pyversions/pylibjpeg-libjpeg.svg)](https://img.shields.io/pypi/pyversions/pylibjpeg-libjpeg.svg)

## pylibjpeg-libjpeg

A Python 3.7+ wrapper for Thomas Richter's
[libjpeg](https://github.com/thorfdbg/libjpeg), with a focus on use as a
plugin for [pylibjpeg](http://github.com/pydicom/pylibjpeg).

Linux, MacOS and Windows are all supported.

### Installation
#### Dependencies
[NumPy](http://numpy.org)

#### Installing the current release
```bash
pip install pylibjpeg-libjpeg
```
#### Installing the development version

Make sure [Python](https://www.python.org/) and [Git](https://git-scm.com/) are installed. For Windows, you also need to install
[Microsoft's C++ Build Tools](https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16).
```bash
git clone --recurse-submodules https://github.com/pydicom/pylibjpeg-libjpeg
python -m pip install pylibjpeg-libjpeg
```

### Supported JPEG Formats
#### Decoding

| ISO/IEC Standard | ITU Equivalent | JPEG Format |
| --- | --- | --- |
| [10918](https://www.iso.org/standard/18902.html) | [T.81](https://www.itu.int/rec/T-REC-T.81/en) | [JPEG](https://jpeg.org/jpeg/index.html)    |
| [14495](https://www.iso.org/standard/22397.html)   | [T.87](https://www.itu.int/rec/T-REC-T.87/en) | [JPEG-LS](https://jpeg.org/jpegls/index.html) |
| [18477](https://www.iso.org/standard/62552.html)   | | [JPEG XT](https://jpeg.org/jpegxt/) |

#### Encoding
Encoding of JPEG images is not currently supported

### Supported Transfer Syntaxes
#### Decoding
| UID | Description |
| --- | --- |
| 1.2.840.10008.1.2.4.50 | JPEG Baseline (Process 1) |
| 1.2.840.10008.1.2.4.51 | JPEG Extended (Process 2 and 4) |
| 1.2.840.10008.1.2.4.57 | JPEG Lossless, Non-Hierarchical (Process 14) |
| 1.2.840.10008.1.2.4.70 | JPEG Lossless, Non-Hierarchical, First-Order Prediction (Process 14 [Selection Value 1]) |
| 1.2.840.10008.1.2.4.80 | JPEG-LS Lossless |
| 1.2.840.10008.1.2.4.81 | JPEG-LS Lossy (Near-Lossless) Image Compression |

### Usage
#### With pylibjpeg and pydicom

```python
from pydicom import dcmread
from pydicom.data import get_testdata_file

ds = dcmread(get_testdata_file('JPEG-LL.dcm'))
arr = ds.pixel_array
```

#### Standalone JPEG decoding

You can also decode JPEG images to a [numpy ndarray][1]:

[1]: https://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.html

```python
from libjpeg import decode

with open('filename.jpg', 'rb') as f:
    # Returns a numpy array
    arr = decode(f.read())

# Or simply...
arr = decode('filename.jpg')
```
