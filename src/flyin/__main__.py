"""Enables running the package with `python -m flyin`."""

import sys

from .main import main


if __name__ == "__main__":
    sys.exit(main())
