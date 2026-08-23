# -*- coding: utf-8 -*-
import logging
import ssl
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import certifi
import feedparser
import requests
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import AuthorityInformationAccessOID, ExtensionOID
from cryptography.x509.verification import PolicyBuilder, Store
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from scrapling.fetchers import StealthyFetcher
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


log = logging.getLogger(__name__)

# Browser-like request headers. Some hosts sit behind a WAF that answers a GET
# without an Accept header with "415 Unsupported Media Type", so send the same
# set a browser would.
USER_AGENT = "Mozilla Firefox Mozilla/5.0; metaodi website-monitor at github"
ACCEPT_HTML = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
ACCEPT_FEED = (
    "application/rss+xml, application/atom+xml, application/xml;q=0.9, "
    "text/xml;q=0.9, */*;q=0.8"
)
ACCEPT_JSON = "application/json, */*;q=0.8"

# How many AIA hops to follow when completing a truncated certificate chain.
AIA_MAX_DEPTH = 4

# host/port -> path of a CA bundle that completes the chain (None = not fixable)
_aia_bundles = {}


def _headers(accept=None):
    return {
        "user-agent": USER_AGENT,
        "accept": accept or ACCEPT_HTML,
        "accept-language": "de-CH,de;q=0.9,en;q=0.8",
    }


def _aia_issuer_urls(cert):
    """Return the "CA Issuers" URIs from a certificate's AIA extension."""
    try:
        aia = cert.extensions.get_extension_for_oid(
            ExtensionOID.AUTHORITY_INFORMATION_ACCESS
        ).value
    except x509.ExtensionNotFound:
        return []
    return [
        desc.access_location.value
        for desc in aia
        if desc.access_method == AuthorityInformationAccessOID.CA_ISSUERS
        and isinstance(desc.access_location, x509.UniformResourceIdentifier)
    ]


def _fetch_cert(uri):
    """Download the certificate an AIA "CA Issuers" URI points at."""
    r = requests.get(uri, headers={"user-agent": USER_AGENT}, timeout=10)
    r.raise_for_status()
    try:
        return x509.load_der_x509_certificate(r.content)
    except ValueError:
        return x509.load_pem_x509_certificate(r.content)


def _collect_intermediates(leaf):
    """Follow the AIA chain upwards, collecting the certs the server omitted.

    Self-signed certificates (roots) are deliberately never collected: trust
    anchors must come from certifi, not from a certificate we downloaded.
    """
    collected = []
    cert = leaf
    for _ in range(AIA_MAX_DEPTH):
        issuer = None
        for uri in _aia_issuer_urls(cert):
            try:
                issuer = _fetch_cert(uri)
                break
            except Exception as e:
                log.debug(f"Could not fetch AIA certificate {uri}: {e}")
        if issuer is None or issuer.subject == issuer.issuer:
            break
        collected.append(issuer)
        cert = issuer
    return collected


def _server_leaf_cert(host, port):
    """Return the leaf certificate a host serves, without verifying it."""
    pem = ssl.get_server_certificate((host, port), timeout=20)
    return x509.load_pem_x509_certificate(pem.encode("ascii"))


def _build_aia_bundle(host, port):
    """Build a CA bundle that completes ``host``'s chain, or None.

    This is what browsers do when a server forgets to send its intermediate
    certificates: fetch the missing ones through the AIA extension and use
    them to complete the chain.

    The fetched certificates are only used once the chain they produce has
    been verified against certifi's roots, so trust is still anchored in
    certifi and never in the (plain HTTP) AIA download.
    """
    leaf = _server_leaf_cert(host, port)
    intermediates = _collect_intermediates(leaf)
    if not intermediates:
        return None

    root_pem = Path(certifi.where()).read_bytes()
    verifier = (
        PolicyBuilder()
        .store(Store(x509.load_pem_x509_certificates(root_pem)))
        .build_server_verifier(x509.DNSName(host))
    )
    # Raises if the completed chain is not genuine, not yet/no longer valid,
    # or does not match the hostname.
    verifier.verify(leaf, intermediates)

    bundle = Path(tempfile.mkdtemp(prefix="website-monitor-ca-")) / "bundle.pem"
    with open(bundle, "wb") as f:
        f.write(root_pem)
        for cert in intermediates:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
    return str(bundle)


def _aia_ca_bundle(url):
    """Return a cached CA bundle completing ``url``'s chain, or None."""
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        return None

    key = (parts.hostname, parts.port or 443)
    if key not in _aia_bundles:
        try:
            _aia_bundles[key] = _build_aia_bundle(*key)
        except Exception as e:
            log.debug(f"Could not complete certificate chain for {key[0]}: {e}")
            _aia_bundles[key] = None
    return _aia_bundles[key]


def _download_request(url, verify=True, accept=None):
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    headers = _headers(accept)
    try:
        r = http.get(url, headers=headers, timeout=20, verify=verify)
    except requests.exceptions.SSLError:
        # The server may have sent an incomplete certificate chain, which
        # browsers repair transparently but requests does not. Try the same
        # repair once, then give up and let the error through.
        bundle = _aia_ca_bundle(url) if verify is True else None
        if not bundle:
            raise
        log.info(f"Completed incomplete certificate chain for {url} via AIA")
        r = http.get(url, headers=headers, timeout=20, verify=bundle)
    r.raise_for_status()
    return r


def download(url, encoding='utf-8', verify=True):
    r = _download_request(url, verify=verify)
    if encoding:
        r.encoding = encoding
    return r.text


def download_content(url, verify=True):
    r = _download_request(url, verify=verify)
    return r.content


def jsondownload(url, verify=True):
    r = _download_request(url, verify=verify, accept=ACCEPT_JSON)
    return r.json()


def download_file(url, path, verify=True):
    r = _download_request(url, verify=verify)
    with open(path, 'wb') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)


def download_rss(url, verify=True):
    r = _download_request(url, verify=verify, accept=ACCEPT_FEED)
    return feedparser.parse(r.content)


def download_with_selenium(url, selector):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)

    driver.get(url)
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        content = driver.page_source
    except TimeoutException:
        # if the selector was not found return a static string
        log.info(f"selector '{selector}' not found!")
        content = f"selector '{selector}' not found"
    finally:
        driver.quit()

    return content


def download_stealth(url, selector):
    response = StealthyFetcher.fetch(
        url,
        headless=True,
        network_idle=True,
        solve_cloudflare=True,
        wait_selector=selector,
        wait_selector_state="attached",
    )
    return response.html_content
