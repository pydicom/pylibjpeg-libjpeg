# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['libjpeg', 'libjpeg.src.libjpeg', 'libjpeg.tests']

package_data = \
{'': ['*'],
 'libjpeg': ['src/interface/*'],
 'libjpeg.src.libjpeg': ['boxes/*',
                         'cmd/*',
                         'codestream/*',
                         'coding/*',
                         'colortrafo/*',
                         'control/*',
                         'dct/*',
                         'interface/*',
                         'io/*',
                         'marker/*',
                         'std/*',
                         'tools/*',
                         'upsampling/*',
                         'vs10.0/jpeg/*',
                         'vs10.0/jpeg/jpeg/*',
                         'vs10.0/jpeg/jpegdll/*',
                         'vs10.0/jpeg/jpeglib/*',
                         'vs12.0/jpeg/*',
                         'vs12.0/jpeg/jpeg/*',
                         'vs12.0/jpeg/jpegdll/*',
                         'vs12.0/jpeg/jpeglib/*']}

install_requires = \
['numpy>=1.24,<2.0']

extras_require = \
{':extra == "tests"': ['pylibjpeg-data @ '
                       'git+https://github.com/pydicom/pylibjpeg-data.git'],
 'dev': ['black>=23.1,<24.0',
         'coverage>=7.3,<8.0',
         'mypy>=1.7,<2.0',
         'pytest>=7.4,<8.0',
         'pytest-cov>=4.1,<5.0'],
 'tests': ['coverage>=7.3,<8.0', 'pytest>=7.4,<8.0', 'pytest-cov>=4.1,<5.0']}

entry_points = \
{'pylibjpeg.jpeg_decoders': ['openjpeg = libjpeg:decode'],
 'pylibjpeg.jpeg_ls_decoders': ['openjpeg = libjpeg:decode'],
 'pylibjpeg.jpeg_xt_decoders': ['openjpeg = libjpeg:decode'],
 'pylibjpeg.pixel_data_decoders': ['1.2.840.10008.1.2.4.50 = '
                                   'libjpeg:decode_pixel_data',
                                   '1.2.840.10008.1.2.4.51 = '
                                   'libjpeg:decode_pixel_data',
                                   '1.2.840.10008.1.2.4.57 = '
                                   'libjpeg:decode_pixel_data',
                                   '1.2.840.10008.1.2.4.70 = '
                                   'libjpeg:decode_pixel_data',
                                   '1.2.840.10008.1.2.4.80 = '
                                   'libjpeg:decode_pixel_data',
                                   '1.2.840.10008.1.2.4.81 = '
                                   'libjpeg:decode_pixel_data']}

setup_kwargs = {
    'name': 'libjpeg',
    'version': '2.0.0.dev0',
    'description': 'A Python framework for decoding JPEG and decoding/encoding DICOMRLE data, with a focus on supporting pydicom',
    'long_description': "[![Build Status](https://github.com/pydicom/pylibjpeg-libjpeg/workflows/unit-tests/badge.svg)](https://github.com/pydicom/pylibjpeg-libjpeg/actions?query=workflow%3Aunit-tests)\n[![codecov](https://codecov.io/gh/pydicom/pylibjpeg-libjpeg/branch/master/graph/badge.svg)](https://codecov.io/gh/pydicom/pylibjpeg-libjpeg)\n[![PyPI version](https://badge.fury.io/py/pylibjpeg-libjpeg.svg)](https://badge.fury.io/py/pylibjpeg-libjpeg)\n[![Python versions](https://img.shields.io/pypi/pyversions/pylibjpeg-libjpeg.svg)](https://img.shields.io/pypi/pyversions/pylibjpeg-libjpeg.svg)\n\n## pylibjpeg-libjpeg\n\nA Python 3.8+ wrapper for Thomas Richter's\n[libjpeg](https://github.com/thorfdbg/libjpeg), with a focus on use as a\nplugin for [pylibjpeg](http://github.com/pydicom/pylibjpeg).\n\nLinux, MacOS and Windows are all supported.\n\n### Installation\n#### Dependencies\n[NumPy](http://numpy.org)\n\n#### Installing the current release\n```bash\npip install pylibjpeg-libjpeg\n```\n#### Installing the development version\n\nMake sure [Python](https://www.python.org/) and [Git](https://git-scm.com/) are installed. For Windows, you also need to install\n[Microsoft's C++ Build Tools](https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16).\n```bash\ngit clone --recurse-submodules https://github.com/pydicom/pylibjpeg-libjpeg\npython -m pip install pylibjpeg-libjpeg\n```\n\n### Supported JPEG Formats\n#### Decoding\n\n| ISO/IEC Standard | ITU Equivalent | JPEG Format |\n| --- | --- | --- |\n| [10918](https://www.iso.org/standard/18902.html) | [T.81](https://www.itu.int/rec/T-REC-T.81/en) | [JPEG](https://jpeg.org/jpeg/index.html)    |\n| [14495](https://www.iso.org/standard/22397.html)   | [T.87](https://www.itu.int/rec/T-REC-T.87/en) | [JPEG-LS](https://jpeg.org/jpegls/index.html) |\n| [18477](https://www.iso.org/standard/62552.html)   | | [JPEG XT](https://jpeg.org/jpegxt/) |\n\n#### Encoding\nEncoding of JPEG images is not currently supported\n\n### Supported Transfer Syntaxes\n#### Decoding\n| UID | Description |\n| --- | --- |\n| 1.2.840.10008.1.2.4.50 | JPEG Baseline (Process 1) |\n| 1.2.840.10008.1.2.4.51 | JPEG Extended (Process 2 and 4) |\n| 1.2.840.10008.1.2.4.57 | JPEG Lossless, Non-Hierarchical (Process 14) |\n| 1.2.840.10008.1.2.4.70 | JPEG Lossless, Non-Hierarchical, First-Order Prediction (Process 14 [Selection Value 1]) |\n| 1.2.840.10008.1.2.4.80 | JPEG-LS Lossless |\n| 1.2.840.10008.1.2.4.81 | JPEG-LS Lossy (Near-Lossless) Image Compression |\n\n### Usage\n#### With pylibjpeg and pydicom\n\n```python\nfrom pydicom import dcmread\nfrom pydicom.data import get_testdata_file\n\nds = dcmread(get_testdata_file('JPEG-LL.dcm'))\narr = ds.pixel_array\n```\n\n#### Standalone JPEG decoding\n\nYou can also decode JPEG images to a [numpy ndarray][1]:\n\n[1]: https://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.html\n\n```python\nfrom libjpeg import decode\n\nwith open('filename.jpg', 'rb') as f:\n    # Returns a numpy array\n    arr = decode(f.read())\n\n# Or simply...\narr = decode('filename.jpg')\n```\n",
    'author': 'pylibjpeg-libjpeg contributors',
    'author_email': 'None',
    'maintainer': 'scaramallion',
    'maintainer_email': 'scaramallion@users.noreply.github.com',
    'url': 'https://github.com/pydicom/pylibjpeg-openjpeg',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}
from build import *
build(setup_kwargs)

setup(**setup_kwargs)
