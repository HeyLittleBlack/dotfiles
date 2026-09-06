"""Run with: python3 tests/test_kitty_title.py"""
from pathlib import Path
from types import SimpleNamespace

config = Path(__file__).resolve().parents[1] / "configs/kitty/kitty.conf"
line = next(line for line in config.read_text().splitlines() if line.startswith("tab_title_template "))
template = compile("f" + line.split(" ", 1)[1], str(config), "eval")
for exe, cwd, expected in (
    ("-zsh", "/work/notes", "1: notes"),
    ("-bash", "/work/notes", "1: notes"),
    ("zsh", "/work/notes/", "1: notes"),
    ("fish", "/", "1: /"),
    ("nvim", "/work/notes", "1: nvim"),
    ("python3", "/work/notes", "1: python3"),
):
    actual = eval(template, {"index": 1, "tab": SimpleNamespace(active_exe=exe, active_wd=cwd)})
    assert actual == expected, (exe, actual, expected)

print("Kitty title checks passed")
