from techdesk import cli
from techdesk.core.diagnostics import WINDOWS_DIAGNOSTICS


def test_menu_has_14_core_support_tools():
    core = cli.MENU_GROUPS["01  |  IT SUPPORT DASHBOARD"]
    assert len(core) == 14
    assert core[0][1] == "Clean temporary files"
    assert core[2][1] == "Verify system files (SFC)"
    assert core[3][1] == "Repair Windows image (DISM)"
    assert core[13][1] == "View key service status"


def test_menu_numbers_are_unique_and_sequential():
    numbers = [int(number) for group in cli.MENU_GROUPS.values() for number, _, _ in group]
    assert sorted(numbers) == list(range(1, 37))
    assert cli.MENU_GROUPS["04  |  AUTOMATED MAINTENANCE"][0][2] == "maintenance"
    assert len(numbers) == len(set(numbers))


def test_system_diagnostic_waits_before_returning_to_menu(monkeypatch):
    inputs = iter(["15", "", "0"])
    prompts = []

    def fake_input(prompt):
        prompts.append(prompt)
        return next(inputs)

    monkeypatch.setattr(cli, "_show_menu", lambda: None)
    monkeypatch.setattr(
        cli,
        "collect_diagnostics",
        lambda: {"system": {"hostname": "TEST-PC"}, "storage": {}},
    )

    assert cli._menu(fake_input) == 0
    assert any("Press ENTER to return to the menu" in prompt for prompt in prompts)


def test_windows_diagnostic_waits_before_returning_to_menu(monkeypatch):
    diagnostic = next(iter(WINDOWS_DIAGNOSTICS))
    number = next(
        number
        for entries in cli.MENU_GROUPS.values()
        for number, _, topic in entries
        if topic == diagnostic
    )
    inputs = iter([number, "", "0"])
    prompts = []

    def fake_input(prompt):
        prompts.append(prompt)
        return next(inputs)

    monkeypatch.setattr(cli, "_show_menu", lambda: None)
    monkeypatch.setattr(cli, "run_windows_diagnostic", lambda _: "TEST DIAGNOSTIC")

    assert cli._menu(fake_input) == 0
    assert any("Press ENTER to return to the menu" in prompt for prompt in prompts)



def test_maintenance_menu_is_reachable_and_returns_to_main_menu(monkeypatch):
    inputs = iter(["36", "0", "0"])
    monkeypatch.setattr(cli, "_show_menu", lambda: None)
    monkeypatch.setattr(cli, "_maintenance_menu", lambda input_fn: None)

    assert cli._menu(lambda _prompt: next(inputs)) == 0
