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

    # Tests don't want to actually wait out the selector-not-found retry delay.
    monkeypatch.setattr(website_hash.time, "sleep", lambda seconds: None)

    def _setup(*, static_html=None, static_html_sequence=None, rss_feed=None):
        if static_html_sequence is not None:
            responses = iter(static_html_sequence)
            fetch = lambda *args, **kwargs: next(responses)
            monkeypatch.setattr(website_hash.dl, "download", fetch)
            monkeypatch.setattr(website_hash.dl, "download_with_selenium", fetch)
        elif static_html is not None:
            monkeypatch.setattr(website_hash.dl, "download", lambda url, verify=True: static_html)
            monkeypatch.setattr(
                website_hash.dl,
                "download_with_selenium",
                lambda url, selector: static_html,
            )
        if rss_feed is not None:
            monkeypatch.setattr(website_hash.dl, "download_rss", lambda url, verify=True: rss_feed)

    return _setup


# ---------------------------------------------------------------------------
# Certificate fixtures (for AIA chain completion)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def cert_chain():
    """Return a (leaf, intermediate, root) chain built in memory.

    The leaf points at the intermediate and the intermediate at the root via
    their AIA "CA Issuers" extension, mirroring the layout of a real chain.
    """
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import AuthorityInformationAccessOID, NameOID

    now = datetime.datetime.now(datetime.timezone.utc)

    def build(common_name, issuer_cert=None, issuer_key=None, aia_url=None, ca=True):
        key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer_cert.subject if issuer_cert else subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=30))
            .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
        )
        if aia_url:
            builder = builder.add_extension(
                x509.AuthorityInformationAccess([
                    x509.AccessDescription(
                        AuthorityInformationAccessOID.CA_ISSUERS,
                        x509.UniformResourceIdentifier(aia_url),
                    )
                ]),
                critical=False,
            )
        cert = builder.sign(issuer_key or key, hashes.SHA256())
        return cert, key

    root, root_key = build("Test Root CA")
    intermediate, intermediate_key = build(
        "Test Intermediate CA",
        issuer_cert=root,
        issuer_key=root_key,
        aia_url="http://ca.example.com/root",
    )
    leaf, _ = build(
        "leaf.example.com",
        issuer_cert=intermediate,
        issuer_key=intermediate_key,
        aia_url="http://ca.example.com/intermediate",
        ca=False,
    )
    return leaf, intermediate, root
