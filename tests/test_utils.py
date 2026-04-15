# -*- coding: utf-8 -*-
"""Tests for lib/utils.py."""

import utils


class TestSanitizeLabelForFilename:
    def test_simple_label(self):
        assert utils.sanitize_label_for_filename("EBP Insights") == "ebp_insights"

    def test_domain_name(self):
        assert utils.sanitize_label_for_filename("stefanoderbolz.ch") == "stefanoderbolz_ch"

    def test_already_clean(self):
        assert utils.sanitize_label_for_filename("hello") == "hello"

    def test_uppercase(self):
        assert utils.sanitize_label_for_filename("HELLO WORLD") == "hello_world"

    def test_special_characters(self):
        # Trailing special chars are stripped (consecutive underscores collapsed, then filtered)
        assert utils.sanitize_label_for_filename("foo@bar#baz!") == "foo_bar_baz"

    def test_consecutive_special_chars(self):
        # Multiple special chars in a row should produce a single underscore
        assert utils.sanitize_label_for_filename("a...b") == "a_b"

    def test_hyphens_preserved(self):
        assert utils.sanitize_label_for_filename("my-website") == "my-website"

    def test_underscores_preserved(self):
        assert utils.sanitize_label_for_filename("my_label") == "my_label"

    def test_mixed_separators(self):
        # Unicode letters like ü are preserved by str.isalnum()
        assert utils.sanitize_label_for_filename("Gemeinde Rüschlikon – News") == "gemeinde_rüschlikon_news"

    def test_empty_string(self):
        assert utils.sanitize_label_for_filename("") == ""

    def test_only_special_chars(self):
        assert utils.sanitize_label_for_filename("...") == ""
