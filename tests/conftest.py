# -*- coding: utf-8 -*-
"""Shared pytest fixtures for website-monitor tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import feedparser
import pytest

# Add the lib directory to sys.path so that `import download as dl`
# inside website_hash.py resolves correctly.
LIB_DIR = str(Path(__file__).resolve().parent.parent / "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


# ---------------------------------------------------------------------------
# Raw fixture content helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def static_simple_html():
    """Return HTML content from the simple static fixture."""
    return (FIXTURES_DIR / "static_simple.html").read_text(encoding="utf-8")


@pytest.fixture
def static_multi_html():
    """Return HTML content with multiple <article> elements."""
    return (FIXTURES_DIR / "static_multi.html").read_text(encoding="utf-8")


@pytest.fixture
def rss_feed_bytes():
    """Return raw bytes of the RSS 2.0 fixture."""
    return (FIXTURES_DIR / "rss_feed.xml").read_bytes()


@pytest.fixture
def atom_feed_bytes():
    """Return raw bytes of the Atom fixture."""
    return (FIXTURES_DIR / "atom_feed.xml").read_bytes()


@pytest.fixture
def rss_no_channel_link_bytes():
    """Return raw bytes of an RSS feed without a channel link."""
    return (FIXTURES_DIR / "rss_no_channel_link.xml").read_bytes()


# ---------------------------------------------------------------------------
# Parsed feed fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rss_parsed_feed(rss_feed_bytes):
    """Return a feedparser result for the RSS 2.0 fixture."""
    return feedparser.parse(rss_feed_bytes)


@pytest.fixture
def atom_parsed_feed(atom_feed_bytes):
    """Return a feedparser result for the Atom fixture."""
    return feedparser.parse(atom_feed_bytes)


@pytest.fixture
def rss_no_channel_link_parsed_feed(rss_no_channel_link_bytes):
    """Return a feedparser result for an RSS feed without a channel link."""
    return feedparser.parse(rss_no_channel_link_bytes)


# ---------------------------------------------------------------------------
# Mock download module helper
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_download(monkeypatch):
    """Return a helper that patches ``download`` (aliased as ``dl``) in website_hash.

    Usage in tests::

        def test_something(mock_download, static_simple_html):
            mock_download(static_html=static_simple_html)
            ...
    """
    import website_hash

    def _setup(*, static_html=None, rss_feed=None):
        if static_html is not None:
            monkeypatch.setattr(website_hash.dl, "download", lambda url, verify=True: static_html)
            monkeypatch.setattr(
                website_hash.dl,
                "download_with_selenium",
                lambda url, selector: static_html,
            )
        if rss_feed is not None:
            monkeypatch.setattr(website_hash.dl, "download_rss", lambda url, verify=True: rss_feed)

    return _setup
