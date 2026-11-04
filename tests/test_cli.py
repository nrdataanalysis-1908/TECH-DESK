from techdesk.cli import MENU_GROUPS


def test_menu_prioritizes_executable_operations():
    entries = [entry for group in MENU_GROUPS.values() for entry in group]
    executable = [entry for entry in entries if entry[2].startswith("operation:")]
    consultations = [entry for entry in entries if not entry[2].startswith("operation:")]
    assert len(executable) == 18
    assert len(consultations) == 12
    assert len(executable) > len(consultations)


def test_menu_numbers_are_unique_and_sequential():
    numbers = [
        int(number)
        for group in MENU_GROUPS.values()
        for number, _, _ in group
    ]
    assert sorted(numbers) == list(range(1, 31))
    assert len(numbers) == len(set(numbers))
