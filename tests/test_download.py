# -*- coding: utf-8 -*-
"""Tests for lib/download.py."""

from unittest.mock import MagicMock, patch

import pytest
import responses

import download as dl


# ---------------------------------------------------------------------------
# download() — static text download
# ---------------------------------------------------------------------------

class TestDownload:
    @responses.activate
    def test_download_returns_text(self):
        responses.add(
            responses.GET,
            "https://example.com/page",
            body="<html><body>Hello</body></html>",
            status=200,
        )
        text = dl.download("https://example.com/page")
        assert "Hello" in text

    @responses.activate
    def test_download_custom_encoding(self):
        responses.add(
            responses.GET,
            "https://example.com/page",
            body="Héllo",
            status=200,
        )
        text = dl.download("https://example.com/page", encoding="utf-8")
        assert "llo" in text

    @responses.activate
    def test_download_no_encoding(self):
        responses.add(
            responses.GET,
            "https://example.com/page",
            body="Hello",
            status=200,
        )
        text = dl.download("https://example.com/page", encoding=None)
        assert isinstance(text, str)


# ---------------------------------------------------------------------------
# download_content() — binary download
# ---------------------------------------------------------------------------

class TestDownloadContent:
    @responses.activate
    def test_download_content_returns_bytes(self):
        responses.add(
            responses.GET,
            "https://example.com/file",
            body=b"\x89PNG",
            status=200,
        )
        content = dl.download_content("https://example.com/file")
        assert isinstance(content, bytes)
        assert content == b"\x89PNG"


# ---------------------------------------------------------------------------
# jsondownload()
# ---------------------------------------------------------------------------

class TestJsonDownload:
    @responses.activate
    def test_json_download(self):
        responses.add(
            responses.GET,
            "https://example.com/api",
            json={"key": "value"},
            status=200,
        )
        data = dl.jsondownload("https://example.com/api")
        assert data == {"key": "value"}


# ---------------------------------------------------------------------------
# download_file()
# ---------------------------------------------------------------------------

class TestDownloadFile:
    @responses.activate
    def test_download_file(self, tmp_path):
        responses.add(
            responses.GET,
            "https://example.com/file.bin",
            body=b"file content",
            status=200,
        )
        out = tmp_path / "downloaded.bin"
        dl.download_file("https://example.com/file.bin", str(out))
        assert out.exists()
        assert out.read_bytes() == b"file content"


# ---------------------------------------------------------------------------
# download_rss()
# ---------------------------------------------------------------------------

class TestDownloadRss:
    @responses.activate
    def test_download_rss_parses_feed(self, rss_feed_bytes):
        responses.add(
            responses.GET,
            "https://example.com/feed.xml",
            body=rss_feed_bytes,
            status=200,
            content_type="application/rss+xml",
        )
        feed = dl.download_rss("https://example.com/feed.xml")
        assert len(feed.entries) == 2
        assert feed.entries[0].title == "First Post"

    @responses.activate
    def test_download_rss_atom(self, atom_feed_bytes):
        responses.add(
            responses.GET,
            "https://example.com/atom.xml",
            body=atom_feed_bytes,
            status=200,
            content_type="application/atom+xml",
        )
        feed = dl.download_rss("https://example.com/atom.xml")
        assert len(feed.entries) == 2
        assert feed.entries[0].title == "Atom Entry 1"


# ---------------------------------------------------------------------------
# _download_request() — error handling
# ---------------------------------------------------------------------------

class TestDownloadRequest:
    @responses.activate
    def test_raises_on_404(self):
        responses.add(
            responses.GET,
            "https://example.com/missing",
            status=404,
        )
        with pytest.raises(Exception):
            dl.download("https://example.com/missing")

    @responses.activate
    def test_verify_false(self):
        responses.add(
            responses.GET,
            "https://example.com/page",
            body="OK",
            status=200,
        )
        text = dl.download("https://example.com/page", verify=False)
        assert text == "OK"
