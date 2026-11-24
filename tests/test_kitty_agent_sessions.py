"""Run with Kitty's Python, compiling this file with optimize=0 to enable assertions."""
import curses
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
from unittest.mock import Mock, patch

from kitty.config import load_config
from kitty.fast_data_types import wcswidth


config = Path(__file__).resolve().parents[1] / "configs/kitty/kitty.conf"
errors = []
options = load_config(str(config), accumulate_bad_lines=errors)
assert not errors, errors
assert any(
    mapping.definition == "kitten agent_sessions.py"
    for bindings in options.keyboard_modes[""].keymap.values()
    for mapping in bindings
)

kitten = runpy.run_path(str(config.with_name("agent_sessions.py")))
processes = [
    ["opencode"],
    ["/bin/codex"],
    ["/bin/codex"],
    ["/home/user/.local/share/claude/versions/2.1.310"],
    ["node", "/lib/node_modules/@earendil-works/pi-coding-agent/dist/cli.js"],
    ["/bin/agy"],
    ["zsh", "codex"],
    ["node", "other.js", "pi"],
]
windows = [{"id": 42, "title": "Project", "cwd": "/project", "foreground_processes": [
    {"cmdline": cmdline, "cwd": "/work"} for cmdline in processes
]}, {"id": 43, "cwd": "/idle", "foreground_processes": [{"cmdline": ["zsh"]}]}]
tree = [{"tabs": [{"windows": windows}]}]
assert list(kitten["agent_sessions"](tree)) == [
    (42, name, "Project", "/work")
    for name in ("OpenCode", "Codex", "Claude", "Pi", "Antigravity")
]

with (
    patch.dict("os.environ", {"KITTY_LISTEN_ON": "unix:/tmp/kitty-test"}),
    patch("subprocess.run", return_value=SimpleNamespace(stdout=json.dumps(tree))) as remote,
    patch("curses.wrapper", return_value=42) as picker,
):
    assert kitten["main"]([]) == 42
    assert remote.call_args.args[0][1:] == ["@", "--to", "unix:/tmp/kitty-test", "ls"]
    assert picker.call_args.args[0] is kitten["choose_session"]

sessions = [(index, "Codex", f"Window {index}", "/work") for index in range(3)]
screen = Mock()
draw = kitten["draw_session_row"]
draw(screen, 0, 79, curses.A_BOLD, "Agent", "Window title", "Working directory")
draw(screen, 1, 79, curses.A_REVERSE, "Codex", "窗格标题" * 8, "/work")
header, row = (screen.addstr.call_args_list[:3], screen.addstr.call_args_list[3:])
assert [call.args[1] for call in header] == [call.args[1] for call in row] == [2, 17, 48]
assert wcswidth(row[1].args[2]) <= 29
screen.reset_mock()
draw(screen, 0, 20, curses.A_NORMAL, "Codex", "窗格标题", "/work")
assert all(call.args[1] + wcswidth(call.args[2]) <= 20 for call in screen.addstr.call_args_list)
screen.getmaxyx.return_value = (9, 80)
with (
    patch("curses.set_escdelay"),
    patch("curses.use_default_colors") as default_colors,
    patch("curses.init_pair"),
    patch("curses.color_pair", return_value=0),
    patch("curses.curs_set") as cursor,
):
    for keys, expected in (
        ([curses.KEY_UP, curses.KEY_DOWN, curses.KEY_DOWN, curses.KEY_DOWN, "\n"], 2),
        (["j", "l", "h", "k", "\r"], 0),
        ([curses.KEY_RIGHT, curses.KEY_LEFT, "\x1b"], None),
        (["/", "w", "2", "x", "\n", curses.KEY_BACKSPACE, "\n"], 2),
        (["/", "w", "2", " ", "x", " ", "\x17", "\n"], 2),
        (["/", "w", "2", "\x15", "\n"], 0),
    ):
        screen.get_wch.side_effect = keys
        assert kitten["choose_session"](screen, sessions) == expected

    assert default_colors.call_count == 6
    screen.chgat.assert_any_call(5, 1, 78, curses.A_BOLD | curses.A_REVERSE)
    assert cursor.call_args_list[0].args == (0,)
    assert cursor.call_args_list[-1].args == (1,)
    screen.move.assert_called_with(1, len("  Search: "))
    screen.get_wch.side_effect = ["/", "o", "p", "n", "c", "\n"]
    assert kitten["choose_session"](screen, [
        (1, "Codex", "opnc", "/work"),
        (2, "OpenCode", "Project", "/work"),
    ]) == 2
assert kitten["matches_query"]("Claude 中文标题 /my/repo", "cld 中文 mrp")

calls = []
boss = SimpleNamespace(
    window_id_map={42: object()},
    set_active_window=lambda window_id, **kwargs: calls.append((window_id, kwargs)),
)
for answer in (None, 43, 42):
    kitten["handle_result"]([], answer, 1, boss)
assert calls == [(42, {"switch_os_window_if_needed": True})]

print("Kitty agent session checks passed")
