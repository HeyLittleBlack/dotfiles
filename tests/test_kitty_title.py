"""Run with: python3 tests/test_kitty_title.py"""
from pathlib import Path
import runpy
from types import SimpleNamespace
import kitty.fast_data_types

config = Path(__file__).resolve().parents[1] / "configs/kitty/kitty.conf"
assert 'tab_title_template "{custom}"' in config.read_text().splitlines()
draw_title = runpy.run_path(str(config.with_name("tab_bar.py")))["draw_title"]
original_get_boss = kitty.fast_data_types.get_boss
for name, cwd, expected in (
    ("", "/work/notes", "1: notes"),
    ("", "/work/notes/", "1: notes"),
    ("", "/", "1: /"),
    ("server", "/work/notes", "1: server"),
):
    kitty.fast_data_types.get_boss = lambda: SimpleNamespace(
        tab_for_id=lambda _: SimpleNamespace(name=name)
    )
    actual = draw_title({"index": 1, "tab_id": 42, "tab": SimpleNamespace(active_wd=cwd)})
    assert actual == expected, (name, cwd, actual, expected)
kitty.fast_data_types.get_boss = original_get_boss

print("Kitty title checks passed")
