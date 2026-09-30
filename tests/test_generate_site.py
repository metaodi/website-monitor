from workflow.generate_site import generate_html


def test_generate_html_includes_search_and_title_suggestions(tmp_path):
    entries = [
        {
            "timestamp": "2026-04-13T14:20:44.356775+00:00",
            "label": "Council & News",
            "url": "https://example.com",
            "csv_source": "thalwil",
            "diff_preview": "New announcement with searchable details",
        },
        {
            "timestamp": "2026-04-12T14:20:44.356775+00:00",
            "label": "Council & News",
            "url": "https://example.com",
            "csv_source": "thalwil",
            "diff_preview": "Another announcement",
        },
    ]

    generate_html(entries, [], tmp_path, "https://example.com")

    page = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert '<input type="search" id="notification-search"' in page
    assert '<option value="Council &amp; News">' in page
    assert page.count('<option value="Council &amp; News">') == 1
    assert 'data-search="Council &amp; News thalwil https://example.com New announcement with searchable details"' in page
    assert "article.dataset.search.toLocaleLowerCase().includes(query)" in page
    assert "No matching notifications." in page
