import sys

# Add the pylibjpeg testing data to libjpeg (if available)
try:
    import ljdata as _data

    globals()["data"] = _data
    # Add to cache - needed for pytest
    sys.modules["libjpeg.data"] = _data
except ImportError:
    pass
