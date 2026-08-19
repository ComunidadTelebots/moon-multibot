"""Validation helpers for dashboard-managed Python plugin filenames."""

import re


_PLUGIN_FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,126}\.py")


def validate_plugin_filename(value):
    """Return a safe, plain plugin filename or raise ``ValueError``.

    Plugin management deliberately accepts filenames rather than paths.  Being
    strict here also keeps Windows separators and alternate path spellings out.
    """
    if not isinstance(value, str) or not _PLUGIN_FILENAME.fullmatch(value):
        raise ValueError("nombre de plugin no válido")
    return value
