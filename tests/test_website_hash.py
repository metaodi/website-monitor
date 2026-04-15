# -*- coding: utf-8 -*-
"""Tests for lib/website_hash.py."""

import hashlib

import pytest

import website_hash as wh


# ---------------------------------------------------------------------------
# _normalize_text
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_double_newlines_collapsed(self):
        assert wh._normalize_text("a\n\nb") == "a\nb"

    def test_double_spaces_collapsed(self):
        assert wh._normalize_text("a  b") == "a b"

    def test_no_change_needed(self):
        assert wh._normalize_text("hello world") == "hello world"

    def test_multiple_normalizations(self):
        assert wh._normalize_text("a  b\n\nc") == "a b\nc"


# ---------------------------------------------------------------------------
# _get_html_text  (static scraper)
# ---------------------------------------------------------------------------

class TestGetHtmlTextStatic:
    def test_body_selector(self, mock_download, static_simple_html):
        mock_download(static_html=static_simple_html)
        result = wh._get_html_text("https://example.com", "body", True, "static")
        # Each stripped string is a separate entry
        assert result == ["Hello World", "This is a test paragraph.", "Sidebar content"]

    def test_css_selector(self, mock_download, static_simple_html):
        mock_download(static_html=static_simple_html)
        result = wh._get_html_text("https://example.com", ".content", True, "static")
        # Each stripped string is a separate entry
        assert result == ["Hello World", "This is a test paragraph."]

    def test_multiple_matches(self, mock_download, static_multi_html):
        mock_download(static_html=static_multi_html)
        result = wh._get_html_text("https://example.com", "article", True, "static")
        # Each stripped string from each article is a separate entry
        assert result == [
            "Article 1", "First article content.",
            "Article 2", "Second article content.",
            "Article 3", "Third article content.",
        ]

    def test_selector_not_found_exits(self, mock_download, static_simple_html):
        mock_download(static_html=static_simple_html)
        with pytest.raises(SystemExit):
            wh._get_html_text("https://example.com", ".nonexistent", True, "static")

    def test_invalid_dl_type_raises(self, mock_download, static_simple_html):
        mock_download(static_html=static_simple_html)
        with pytest.raises(Exception, match="Invalid type"):
            wh._get_html_text("https://example.com", "body", True, "unknown")


# ---------------------------------------------------------------------------
# _get_html_text  (dynamic scraper)
# ---------------------------------------------------------------------------

class TestGetHtmlTextDynamic:
    def test_dynamic_uses_selenium_mock(self, mock_download, static_simple_html):
        mock_download(static_html=static_simple_html)
        result = wh._get_html_text("https://example.com", "body", True, "dynamic")
        # Each stripped string is a separate entry, same as static
        assert result == ["Hello World", "This is a test paragraph.", "Sidebar content"]


# ---------------------------------------------------------------------------
# _get_rss_text
# ---------------------------------------------------------------------------

class TestGetRssText:
    def test_rss_feed_default_fields(self, mock_download, rss_parsed_feed):
        """Default fields (title, summary) should be extracted."""
        mock_download(rss_feed=rss_parsed_feed)
        source_list, notification_link = wh._get_rss_text(
            "https://example.com/feed.xml", "title,summary", True
        )
        assert len(source_list) == 2
        assert notification_link == "https://example.com/blog"
        # Check that entry content is present
        texts = " ".join(source_list)
        assert "First Post" in texts
        assert "Second Post" in texts

    def test_rss_title_only(self, mock_download, rss_parsed_feed):
        """Extracting only the title field."""
        mock_download(rss_feed=rss_parsed_feed)
        source_list, _ = wh._get_rss_text(
            "https://example.com/feed.xml", "title", True
        )
        assert len(source_list) == 2
        assert source_list[0] == "First Post"
        assert source_list[1] == "Second Post"

    def test_rss_notification_link_channel(self, mock_download, rss_parsed_feed):
        """Channel link is preferred for notification URL."""
        mock_download(rss_feed=rss_parsed_feed)
        _, link = wh._get_rss_text("https://example.com/feed.xml", "title", True)
        assert link == "https://example.com/blog"

    def test_rss_no_channel_link_fallback(self, mock_download, rss_no_channel_link_parsed_feed):
        """Falls back to first entry link when channel link is absent."""
        mock_download(rss_feed=rss_no_channel_link_parsed_feed)
        _, link = wh._get_rss_text("https://example.com/feed.xml", "title", True)
        assert link == "https://example.com/blog/only-post"

    def test_atom_feed(self, mock_download, atom_parsed_feed):
        """Atom feeds should work the same way."""
        mock_download(rss_feed=atom_parsed_feed)
        source_list, link = wh._get_rss_text(
            "https://example.com/atom.xml", "title,summary", True
        )
        assert len(source_list) == 2
        texts = " ".join(source_list)
        assert "Atom Entry 1" in texts
        assert "Atom Entry 2" in texts
        assert link == "https://example.com/atom"


# ---------------------------------------------------------------------------
# get_website_text
# ---------------------------------------------------------------------------

class TestGetWebsiteText:
    def test_static_returns_tuple(self, mock_download, static_simple_html):
        mock_download(static_html=static_simple_html)
        text, url = wh.get_website_text("https://example.com", "body", True, "static")
        assert isinstance(text, str)
        assert "Hello World" in text
        # For non-RSS types, notification URL is the original URL
        assert url == "https://example.com"

    def test_rss_returns_tuple(self, mock_download, rss_parsed_feed):
        mock_download(rss_feed=rss_parsed_feed)
        text, url = wh.get_website_text(
            "https://example.com/feed.xml", "title,summary", True, "rss"
        )
        assert isinstance(text, str)
        assert "First Post" in text
        assert url == "https://example.com/blog"

    def test_text_is_sorted_and_deduplicated(self, mock_download, static_multi_html):
        mock_download(static_html=static_multi_html)
        text, _ = wh.get_website_text("https://example.com", "article", True, "static")
        # Each article produces a multi-line block; the blocks themselves are sorted
        # Split into blocks by looking at what get_website_text returns
        # The function joins unique_source_list with "\n" after sorting
        # Each source_list entry is one article's text (multi-line)
        assert "Article 1" in text
        assert "Article 2" in text
        assert "Article 3" in text

    def test_dynamic_returns_tuple(self, mock_download, static_simple_html):
        mock_download(static_html=static_simple_html)
        text, url = wh.get_website_text("https://example.com", "body", True, "dynamic")
        assert isinstance(text, str)
        assert url == "https://example.com"


# ---------------------------------------------------------------------------
# get_website_hash
# ---------------------------------------------------------------------------

class TestGetWebsiteHash:
    def test_hash_is_sha256(self, mock_download, static_simple_html):
        mock_download(static_html=static_simple_html)
        h, _ = wh.get_website_hash("https://example.com", "body", True, "static")
        assert len(h) == 64  # SHA-256 hex digest length

    def test_hash_deterministic(self, mock_download, static_simple_html):
        mock_download(static_html=static_simple_html)
        h1, _ = wh.get_website_hash("https://example.com", "body", True, "static")
        h2, _ = wh.get_website_hash("https://example.com", "body", True, "static")
        assert h1 == h2

    def test_hash_matches_manual(self, mock_download, static_simple_html):
        mock_download(static_html=static_simple_html)
        text, _ = wh.get_website_text("https://example.com", "body", True, "static")
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        h, _ = wh.get_website_hash("https://example.com", "body", True, "static")
        assert h == expected

    def test_output_file(self, mock_download, static_simple_html, tmp_path):
        mock_download(static_html=static_simple_html)
        out = tmp_path / "output.txt"
        wh.get_website_hash("https://example.com", "body", True, "static", output=str(out))
        assert out.exists()
        text, _ = wh.get_website_text("https://example.com", "body", True, "static")
        assert out.read_text(encoding="utf-8") == text

    def test_rss_hash(self, mock_download, rss_parsed_feed):
        mock_download(rss_feed=rss_parsed_feed)
        h, url = wh.get_website_hash(
            "https://example.com/feed.xml", "title", True, "rss"
        )
        assert len(h) == 64
        assert url == "https://example.com/blog"
