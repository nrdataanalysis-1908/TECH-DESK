from pathlib import Path

from techdesk.core.support_tools import download_https_file


class FakeResponse:
    def __init__(self, body, content_length):
        self.body = body
        self.headers = {"Content-Length": content_length}
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def geturl(self):
        return "https://example.com/file.bin"

    def read(self, size):
        chunk = self.body[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


class FakeOpener:
    def __init__(self, response):
        self.response = response

    def open(self, request, timeout):
        return self.response


def test_download_rejects_truncated_body_when_content_length_is_larger(tmp_path, monkeypatch):
    import urllib.request

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        urllib.request,
        "build_opener",
        lambda *args: FakeOpener(FakeResponse(b"abc", "5")),
    )

    result = download_https_file("https://example.com/file.bin")

    assert result.success is False
    assert "Content-Length" in result.message
    assert not (tmp_path / "Downloads" / "file.bin.part").exists()


def test_download_rejects_malformed_content_length(tmp_path, monkeypatch):
    import urllib.request

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        urllib.request,
        "build_opener",
        lambda *args: FakeOpener(FakeResponse(b"abc", "three")),
    )

    result = download_https_file("https://example.com/file.bin")

    assert result.success is False
    assert "Content-Length" in result.message
