#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hash of a website selector

Usage:
  website_hash.py --url <url-of-website> [--selector <css-selector>] [--output <path>] [--type <type>] [--notify-url-output <path>] [--verbose] [--no-verify]
  website_hash.py (-h | --help)
  website_hash.py --version

Options:
  -h, --help                              Show this screen.
  --version                               Show version.
  -u, --url <url-of-website>              URL of the website to monitor.
  -s, --selector <css-selector>           CSS selector to check for changes [default: body].
  -t, --type <type>                       Type of website, one of: static, dynamic, rss [default: static].
  -o, --output <path>                     Save the selector output to a file.
  -n, --notify-url-output <path>          Save the notification URL to a file.
  --verbose                               Option to enable more verbose output.
  --no-verify                             Option to disable SSL verification for requests.
"""


import hashlib
import logging
import re
import sys
from pprint import pformat
from bs4 import BeautifulSoup
from docopt import docopt
import urllib3
import download as dl

log = logging.getLogger(__name__)

_WORD_RE = re.compile(r"\w")


def _normalize_text(text):
    """Normalize whitespace in extracted text."""
    text = text.replace("\n\n", "\n")
    text = text.replace("  ", " ")
    return text


def _strip_html(text):
    """Strip HTML tags from text using BeautifulSoup, returning cleaned text."""
    soup = BeautifulSoup(text, "html.parser")
    return "\n".join(soup.stripped_strings)


def _get_rss_text(url, selector, verify):
    """Extract text from an RSS/Atom feed.

    Args:
        url: URL of the RSS/Atom feed
        selector: Comma-separated list of entry fields to extract (e.g. 'title,link').
                  Falls back to 'title' if set to a generic HTML selector like 'body'.
        verify: Whether to verify SSL certificates

    Returns:
        Tuple of (source_list, notification_link) where source_list is a list of
        extracted text strings and notification_link is the channel link from the
        feed (or the first entry's link if no channel link is available, or the
        feed URL as a last resort).
    """
    feed = dl.download_rss(url, verify=verify)

    if feed.bozo and not feed.entries:
        log.error(f"Failed to parse feed at {url}: {feed.bozo_exception}")
        sys.exit(1)

    # Prefer the channel-level link; fall back to the first entry's link
    notification_link = feed.feed.get("link", "")
    if not notification_link and feed.entries:
        notification_link = feed.entries[0].get("link", "")
    if not notification_link:
        notification_link = url

    # Determine which fields to extract from each entry
    fields = ["title", "summary"]
    if selector:
        fields = [f.strip() for f in selector.split(",")]

    source_list = []
    for entry in feed.entries:
        log.debug(entry)
        parts = []
        for field in fields:
            value = entry.get(field, "")
            if value:
                parts.append(_strip_html(str(value)))
        text = _normalize_text(" ".join(parts))
        if _WORD_RE.search(text):
            source_list.append(text)

    if not source_list:
        log.error(f"No entries found in feed at {url}")
        sys.exit(1)

    return source_list, notification_link


def _get_html_text(url, selector, verify, dl_type):
    """Extract text from an HTML page using a CSS selector.

    Args:
        url: URL of the website to check
        selector: CSS selector to extract text from
        verify: Whether to verify SSL certificates
        dl_type: Type of download (static or dynamic)

    Returns:
        List of extracted text strings
    """
    if dl_type == "static":
        content = dl.download(url, verify=verify)
    elif dl_type == "dynamic":
        content = dl.download_with_selenium(url, selector)
    else:
        raise Exception(f"Invalid type: {dl_type}")

    soup = BeautifulSoup(content, "html.parser")
    as_list = soup.select(selector)
    if not as_list:
        log.error(f"Selector {selector} not found in {url}")
        sys.exit(1)

    source_list = []
    for elem in as_list:
        text = _normalize_text("\n".join(elem.stripped_strings))
        if _WORD_RE.search(text):
            source_list.append(text)

    return source_list


def get_website_text(url, selector, verify, dl_type="static"):
    """Extract text from a website selector or RSS feed.

    Args:
        url: URL of the website or feed to check
        selector: CSS selector for HTML pages, or comma-separated field names for RSS feeds
        verify: Whether to verify SSL certificates
        dl_type: Type of download (static, dynamic, or rss)

    Returns:
        Tuple of (source_text, notification_url) where source_text is the
        extracted and normalized text, and notification_url is the URL to use
        in notifications (for RSS feeds, this is the channel link;
        for other types, this is the original URL).
    """
    notification_url = url
    if dl_type == "rss":
        source_list, notification_url = _get_rss_text(url, selector, verify)
    else:
        source_list = _get_html_text(url, selector, verify, dl_type)

    unique_source_list = list(set(source_list))
    log.debug("Unsorted:")
    log.debug(pformat(unique_source_list))

    unique_source_list.sort()
    log.debug("Sorted:")
    log.debug(pformat(unique_source_list))

    source_text = "\n".join(unique_source_list)
    return source_text, notification_url


def get_website_hash(url, selector, verify, dl_type="static", output=None):
    """Get hash of text extracted from a website selector.

    Args:
        url: URL of the website to check
        selector: CSS selector to extract text from
        verify: Whether to verify SSL certificates
        dl_type: Type of download (static or dynamic)
        output: Optional file path to save the extracted text

    Returns:
        Tuple of (hash, notification_url) where hash is the SHA256 hash of
        the extracted text, and notification_url is the URL to use in
        notifications (for RSS feeds, this is the channel link;
        for other types, this is the original URL).
    """
    source_text, notification_url = get_website_text(url, selector, verify, dl_type)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(source_text)
    new_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    return new_hash, notification_url


if __name__ == "__main__":
    arguments = docopt(__doc__, version="Get hash of website 1.0")

    loglevel = logging.INFO
    if arguments["--verbose"]:
        loglevel = logging.DEBUG

    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=loglevel,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.captureWarnings(True)

    url = arguments["--url"]
    selector = arguments["--selector"]
    dl_type = arguments["--type"]
    verify = not arguments["--no-verify"]
    output = arguments["--output"]
    notify_url_output = arguments["--notify-url-output"]

    if not verify:
        urllib3.disable_warnings()

    new_hash, notification_url = get_website_hash(url, selector, verify, dl_type, output)
    log.info(f"Hash: {new_hash}")
    log.info(f"Notification URL: {notification_url}")
    if notify_url_output:
        with open(notify_url_output, "w", encoding="utf-8") as f:
            f.write(notification_url)
    print(new_hash)
