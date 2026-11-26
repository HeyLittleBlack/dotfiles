"""Run with Kitty's Python, compiling with optimize=0 to enable assertions."""
from pathlib import Path
import runpy
from types import SimpleNamespace
import kitty.fast_data_types
from kitty.config import load_config

config = Path(__file__).resolve().parents[1] / "configs/kitty/kitty.conf"
options = load_config(str(config))
assert options.tab_title_template == "{custom}"
assert options.tab_bar_min_tabs == 1
draw_title = runpy.run_path(str(config.with_name("tab_bar.py")))["draw_title"]
original_get_boss = kitty.fast_data_types.get_boss
tab = SimpleNamespace(name="", active_window=SimpleNamespace(id=37))
boss = SimpleNamespace(tab_for_id=lambda _: tab, active_tab=None)
kitty.fast_data_types.get_boss = lambda: boss
try:
    data = {"index": 1, "tab_id": 42, "layout_name": "splits", "num_windows": 2, "max_title_length": 24}
    for name, cwd, expected in (
        ("", "/work/notes", "1: notes"),
        ("", "/work/notes/", "1: notes"),
        ("", "/", "1: /"),
        ("server", "/work/notes", "1: server"),
    ):
        tab.name = name
        data["tab"] = SimpleNamespace(active_wd=cwd)
        assert draw_title(data) == expected

    boss.active_tab = tab
    assert draw_title(data) == "1: server · #37"
    tab.active_window.id = 59
    assert draw_title(data) == "1: server · #59"
    data["layout_name"] = "stack"
    assert draw_title(data) == "1: Z server · #59"
    tab.name = "中文标题" * 8
    title = draw_title(data)
    assert title.endswith("… · #59")
    assert kitty.fast_data_types.wcswidth(title) <= 24
finally:
    kitty.fast_data_types.get_boss = original_get_boss

print("Kitty title checks passed")
