import os
import sys


def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def setup_poppler():
    poppler_bin = resource_path(
        os.path.join("poppler", "Library", "bin")
    )

    if os.path.isdir(poppler_bin):
        os.environ["PATH"] = poppler_bin + os.pathsep + os.environ.get("PATH", "")
