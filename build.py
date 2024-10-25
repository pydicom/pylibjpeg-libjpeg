
import os
from pathlib import Path
import platform
import shutil
from struct import unpack
import subprocess
import sys
from typing import Any, List, Dict


PACKAGE_DIR = Path(__file__).parent / "libjpeg"
LIB_DIR = Path(__file__).parent / "lib"
LIBJPEG_SRC = LIB_DIR / 'libjpeg'
INTERFACE_SRC = LIB_DIR / 'interface'


def build(setup_kwargs: Any) -> Any:
    from setuptools import Extension
    from setuptools.dist import Distribution
    import Cython.Compiler.Options
    from Cython.Build import build_ext, cythonize
    import numpy

    # Compiler and linker arguments
    extra_compile_args = []
    extra_link_args = []
    if platform.system() == 'Windows':
        os.environ['LIB'] = os.path.abspath(
            os.path.join(sys.executable, '../', 'libs')
        )
        extra_compile_args = get_mscv_args()
    elif platform.system() in ['Darwin', 'Linux']:
        # Skip configuration if running with `sdist`
        if 'sdist' not in sys.argv:
            opts = get_gcc_args()
            if sys.byteorder == "big":
                if "-mfpmath=387" in opts["ADDOPTS"]:
                    opts["ADDOPTS"].remove("-mfpmath=387")

            extra_compile_args += opts['ADDOPTS']
            extra_link_args += opts['EXTRA_LIBS']

    macros = [("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")]
    if unpack("h", b"\x00\x01")[0] == 1:
        macros.append(("JPG_BIG_ENDIAN", "1"))

    ext = Extension(
        '_libjpeg',
        [os.fspath(p) for p in get_source_files()],
        language='c++',
        include_dirs=[
            os.fspath(LIBJPEG_SRC),
            os.fspath(INTERFACE_SRC),
            numpy.get_include(),
        ],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        define_macros=macros,
    )

    ext_modules = cythonize(
        [ext],
        include_path=ext.include_dirs,
        language_level=3,
    )

    dist = Distribution({"ext_modules": ext_modules})
    cmd = build_ext(dist)
    cmd.ensure_finalized()
    cmd.run()

    for output in cmd.get_outputs():
        output = Path(output)
        relative_ext = output.relative_to(cmd.build_lib)
        shutil.copyfile(output, relative_ext)

    return setup_kwargs


def get_mscv_args() -> List[str]:
    """Return a list of compiler args for MSVC++'s compiler."""
    flags = [
        '/GS',  # Buffer security check
        '/W3',  # Warning level
        '/Zc:wchar_t',  # Use windows char type
        '/Zc:inline',  # Remove unreferenced function or data (...)
        '/Zc:forScope',
        '/Od',  # Disable optimisation
        '/Oy-',  # (x86 only) don't omit frame pointer
        '/openmp-',  # Disable #pragma omp directive
        '/FC',  # Display full path of source code files
        '/fp:precise',  # Floating-point behaviour
        '/Gd',  # (x86 only) use __cdecl calling convention
        '/GF-',  # Disable string pooling
        '/GR',  # Enable run-time type info
        '/RTC1',  # Enable run-time error checking
        '/MT',  # Create multithreading executable
        # /D defines constants and macros
        '/D_UNICODE',
        '/DUNICODE',
    ]

    # Set the architecture based on system architecture and Python
    is_x64 = platform.architecture()[0] == '64bit'
    if is_x64 and sys.maxsize > 2**32:
        flags.append('/DWIN64=1')
    else:
        # Architecture is 32-bit, or Python is 32-bit
        flags.append('/DWIN32=1')

    return flags


def get_gcc_args() -> Dict[str, str]:
    """Return a list of compiler and linker args for GCC/clang.

    The args are determined by running the src/libjpeg/configure script then
    parsing src/libjpeg/automakefile for the relevant values.

    Returns
    -------
    dict
        A dict with keys COMPILER_CMD, CC_ONLY, SETTINGS, PREFIX,
        PTHREADCFLAGS, PTHREADLDFLAGS, PTHREADLIBS, HWTYPE, HAVE_ADDONS,
        BITSIZE, ADDOPTS, LIB_OPTS, EXTRA_LIBS, CPU, TUNE.
    """
    # Run configure script once
    # Using GCC or clang, run `configure` bash script once
    if 'config.log' not in os.listdir(LIBJPEG_SRC):
        # Needs to be determined before changing the working dir
        fpath = os.path.abspath(LIBJPEG_SRC)
        # Needs to be run from within the src/libjpeg directory
        current_dir = os.getcwd()
        os.chdir(LIBJPEG_SRC)
        subprocess.call([os.path.join(fpath, 'configure')])
        os.chdir(current_dir)

    # Get compilation options
    with open(os.path.join(LIBJPEG_SRC, 'automakefile')) as fp:
        lines = fp.readlines()

    lines = [ll for ll in lines if not ll.startswith('#')]
    opts = [ll.split('=', 1) for ll in lines]
    opts = {vv[0].strip():list(vv[1].strip().split(' ')) for vv in opts}

    return opts


def get_source_files() -> List[Path]:
    """Return a list of paths to the source files to be compiled."""
    source_files = [
        PACKAGE_DIR / '_libjpeg.pyx',
        INTERFACE_SRC /'decode.cpp',
        INTERFACE_SRC /'streamhook.cpp',
    ]
    for p in LIBJPEG_SRC.glob('*/*'):
        if p.suffix == '.cpp':
            source_files.append(p)

    # Source files must always be relative to the setup.py directory
    source_files = [p.relative_to(PACKAGE_DIR.parent) for p in source_files]

    return source_files
