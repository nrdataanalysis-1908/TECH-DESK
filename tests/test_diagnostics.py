from techdesk.core.diagnostics import _format_bytes, collect_diagnostics


def test_format_bytes_handles_missing_value():
    assert _format_bytes(None) is None


def test_format_bytes_formats_gib():
    assert _format_bytes(1024**3) == "1.00 GiB"


def test_collect_diagnostics_returns_expected_sections():
    report = collect_diagnostics()
    assert set(report) == {"sistema", "rede", "armazenamento"}
    assert "sistema_operacional" in report["sistema"]
    assert "enderecos_ip" in report["rede"]
    assert "percentual_utilizado" in report["armazenamento"]
