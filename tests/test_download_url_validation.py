import pytest

from techdesk.core.support_tools import download_https_file


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/file.zip",
        "https://user:secret@example.com/file.zip",
        "https://example.com:8443/file.zip",
        "https://example.com:invalid/file.zip",
        "https://example.com/file.zip\nInjected: value",
        " https://example.com/file.zip",
    ],
)
def test_download_rejects_malformed_https_urls_before_network_io(url, monkeypatch):
    import urllib.request

    def unexpected_network(*args, **kwargs):
        pytest.fail("A URL rejected by validation must not trigger network I/O.")

    monkeypatch.setattr(urllib.request, "build_opener", unexpected_network)

    result = download_https_file(url)

    assert result.success is False
    assert "URL" in result.message
