#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sanitize label to filename

Usage:
  sanitize_label.py <label>
  sanitize_label.py (-h | --help)

Options:
  -h, --help    Show this screen.
"""

import sys
from docopt import docopt


def sanitize_label_for_filename(label):
    """Convert a label to a safe filename."""
    # Replace spaces and special characters with underscores
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in label)
    # Remove consecutive underscores
    safe_name = "_".join(filter(None, safe_name.split("_")))
    return safe_name.lower()


if __name__ == "__main__":
    arguments = docopt(__doc__)
    label = arguments["<label>"]
    print(sanitize_label_for_filename(label))
