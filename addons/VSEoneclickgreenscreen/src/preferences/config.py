from src.common.types.framework import is_extension

__addon_name__ = (
    ".".join(__package__.split(".")[0:3])
    if is_extension()
    else __package__.split(".")[0]
)
