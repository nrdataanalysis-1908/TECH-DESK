import urllib.error

import pytest

from techdesk.core.support_tools import _HTTPSOnlyRedirect


@pytest.mark.parametrize(
    "target",
    [
        "http://example.com/file.zip",
        "https://user:secret@example.com/file.zip",
        "https://example.com:8443/file.zip",
        "https://example.com:invalid/file.zip",
        "https://example.com/file.zip\nInjected: value",
    ],
)
def test_redirect_handler_rejects_noncompliant_https_targets(target):
    handler = _HTTPSOnlyRedirect()

    with pytest.raises(urllib.error.HTTPError):
        handler.redirect_request(None, None, 302, "Found", {}, target)
