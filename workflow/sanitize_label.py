#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sanitize label to filename

Usage:
  sanitize_label.py <label>
  sanitize_label.py (-h | --help)

Options:
  -h, --help    Show this screen.
"""

import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from docopt import docopt
from utils import sanitize_label_for_filename


if __name__ == "__main__":
    arguments = docopt(__doc__)
    label = arguments["<label>"]
    print(sanitize_label_for_filename(label))
