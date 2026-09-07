"""Run with: kitty +runpy 'import runpy; runpy.run_path("tests/test_kitty_copy_or_paste.py")'"""
from pathlib import Path
import runpy
from types import SimpleNamespace
from kitty.config import load_config

kitten = Path(__file__).resolve().parents[1] / "configs/kitty/copy_or_paste.py"
errors = []
options = load_config(str(kitten.with_name("kitty.conf")), accumulate_bad_lines=errors)
assert not errors, errors
for grabbed in (False, True):
    mappings = {m.repeat_count: action for m, action in options.mousemap.items()
                if m.button == 1 and m.mods == 0 and m.grabbed == grabbed}
    assert mappings[1] == "kitten copy_or_paste.py", mappings
    assert -2 not in mappings, mappings

handle_result = runpy.run_path(str(kitten))["handle_result"]
for selected in (True, False):
    calls = []
    window = SimpleNamespace(
        has_selection=lambda: selected,
        copy_to_clipboard=lambda: calls.append("copy"),
        clear_selection=lambda: calls.append("clear"),
    )
    boss = SimpleNamespace(
        window_id_map={1: window},
        paste_from_clipboard=lambda: calls.append("paste"),
    )
    handle_result([], None, 1, boss)
    assert calls == (["copy", "clear"] if selected else ["paste"]), calls
    calls.clear()
    handle_result([], None, 2, boss)
    assert not calls

print("Kitty copy/paste checks passed")
