from techdesk.cli import MENU_GROUPS


def test_menu_has_14_core_support_tools():
    core = MENU_GROUPS["01  |  PAINEL DE SUPORTE TÉCNICO"]
    assert len(core) == 14
    assert core[0][1] == "Limpeza de arquivos temporários"
    assert core[2][1] == "Verificação de arquivos do sistema (SFC)"
    assert core[3][1] == "Reparo da imagem do Windows (DISM)"
    assert core[13][1] == "Ver status dos principais serviços"


def test_menu_numbers_are_unique_and_sequential():
    numbers = [int(number) for group in MENU_GROUPS.values() for number, _, _ in group]
    assert sorted(numbers) == list(range(1, 36))
    assert len(numbers) == len(set(numbers))
