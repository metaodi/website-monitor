#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Shared utility functions for website monitoring"""


def sanitize_label_for_filename(label):
    """Convert a label to a safe filename.

    Args:
        label: The label string to convert

    Returns:
        A sanitized filename-safe string in lowercase

    Examples:
        >>> sanitize_label_for_filename("EBP Insights")
        'ebp_insights'
        >>> sanitize_label_for_filename("stefanoderbolz.ch")
        'stefanoderbolz_ch'
    """
    # Replace spaces and special characters with underscores
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in label)
    # Remove consecutive underscores
    safe_name = "_".join(filter(None, safe_name.split("_")))
    return safe_name.lower()
