from techdesk import cli
from techdesk.core.diagnostics import WINDOWS_DIAGNOSTICS


def test_menu_has_14_core_support_tools():
    core = cli.MENU_GROUPS["01  |  PAINEL DE SUPORTE TÉCNICO"]
    assert len(core) == 14
    assert core[0][1] == "Limpeza de arquivos temporários"
    assert core[2][1] == "Verificação de arquivos do sistema (SFC)"
    assert core[3][1] == "Reparo da imagem do Windows (DISM)"
    assert core[13][1] == "Ver status dos principais serviços"


def test_menu_numbers_are_unique_and_sequential():
    numbers = [int(number) for group in cli.MENU_GROUPS.values() for number, _, _ in group]
    assert sorted(numbers) == list(range(1, 36))
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
        lambda: {"sistema": {"hostname": "TEST-PC"}, "armazenamento": {}},
    )

    assert cli._menu(fake_input) == 0
    assert any("Pressione ENTER para retornar ao menu" in prompt for prompt in prompts)


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
    monkeypatch.setattr(cli, "run_windows_diagnostic", lambda _: "DIAGNÓSTICO TESTE")

    assert cli._menu(fake_input) == 0
    assert any("Pressione ENTER para retornar ao menu" in prompt for prompt in prompts)
