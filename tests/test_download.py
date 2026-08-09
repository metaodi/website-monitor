# -*- coding: utf-8 -*-
"""Tests for lib/download.py."""

from unittest.mock import MagicMock, patch

import pytest
import requests
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


# ---------------------------------------------------------------------------
# Request headers
# ---------------------------------------------------------------------------

class TestRequestHeaders:
    @responses.activate
    def test_download_sends_browser_accept_headers(self):
        """A missing Accept header makes some WAFs answer 415."""
        responses.add(responses.GET, "https://example.com/page", body="OK", status=200)
        dl.download("https://example.com/page")
        headers = responses.calls[0].request.headers
        assert headers["accept"] == dl.ACCEPT_HTML
        assert headers["accept-language"].startswith("de-CH")
        assert headers["user-agent"] == dl.USER_AGENT

    @responses.activate
    def test_download_rss_asks_for_feed_types(self, rss_feed_bytes):
        responses.add(
            responses.GET,
            "https://example.com/feed.xml",
            body=rss_feed_bytes,
            status=200,
            content_type="application/rss+xml",
        )
        dl.download_rss("https://example.com/feed.xml")
        assert responses.calls[0].request.headers["accept"] == dl.ACCEPT_FEED

    @responses.activate
    def test_jsondownload_asks_for_json(self):
        responses.add(responses.GET, "https://example.com/api", json={}, status=200)
        dl.jsondownload("https://example.com/api")
        assert responses.calls[0].request.headers["accept"] == dl.ACCEPT_JSON


# ---------------------------------------------------------------------------
# AIA chain completion
# ---------------------------------------------------------------------------

class TestAiaChainCompletion:
    @responses.activate
    def test_ssl_error_reraised_when_chain_cannot_be_completed(self, monkeypatch):
        monkeypatch.setattr(dl, "_aia_ca_bundle", lambda url: None)
        responses.add(
            responses.GET,
            "https://example.com/page",
            body=requests.exceptions.SSLError("certificate verify failed"),
        )
        with pytest.raises(requests.exceptions.SSLError):
            dl.download("https://example.com/page")

    @responses.activate
    def test_request_retried_once_with_completed_bundle(self, monkeypatch, tmp_path):
        bundle = tmp_path / "bundle.pem"
        bundle.write_text("")
        monkeypatch.setattr(dl, "_aia_ca_bundle", lambda url: str(bundle))
        responses.add(
            responses.GET,
            "https://example.com/page",
            body=requests.exceptions.SSLError("certificate verify failed"),
        )
        responses.add(responses.GET, "https://example.com/page", body="OK", status=200)

        assert dl.download("https://example.com/page") == "OK"
        assert len(responses.calls) == 2

    @responses.activate
    def test_no_repair_attempted_when_verification_is_disabled(self, monkeypatch):
        called = []
        monkeypatch.setattr(dl, "_aia_ca_bundle", lambda url: called.append(url))
        responses.add(
            responses.GET,
            "https://example.com/page",
            body=requests.exceptions.SSLError("boom"),
        )
        with pytest.raises(requests.exceptions.SSLError):
            dl.download("https://example.com/page", verify=False)
        assert called == []

    def test_non_https_urls_are_not_repaired(self):
        assert dl._aia_ca_bundle("http://example.com/page") is None

    def test_collect_intermediates_follows_aia_and_stops_at_root(self, monkeypatch, cert_chain):
        leaf, intermediate, root = cert_chain
        fetched = {
            "http://ca.example.com/intermediate": intermediate,
            "http://ca.example.com/root": root,
        }
        monkeypatch.setattr(dl, "_fetch_cert", lambda uri: fetched[uri])

        collected = dl._collect_intermediates(leaf)

        # The intermediate is collected, the self-signed root never is: trust
        # anchors must come from certifi.
        assert [c.subject for c in collected] == [intermediate.subject]

    def test_collect_intermediates_without_aia_extension(self, cert_chain):
        _, _, root = cert_chain
        assert dl._collect_intermediates(root) == []

    def test_build_bundle_rejects_a_chain_that_does_not_reach_a_root(
        self, monkeypatch, cert_chain
    ):
        """A fetched intermediate signed by an unknown CA must not be trusted."""
        leaf, intermediate, _ = cert_chain
        monkeypatch.setattr(dl, "_server_leaf_cert", lambda host, port: leaf)
        monkeypatch.setattr(dl, "_collect_intermediates", lambda cert: [intermediate])

        with pytest.raises(Exception):
            dl._build_aia_bundle("leaf.example.com", 443)
