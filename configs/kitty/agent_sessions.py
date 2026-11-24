import curses
import json
import locale
import os
from pathlib import PurePath
import re
import subprocess

from kittens.tui.handler import result_handler
from kitty.constants import kitten_exe
from kitty.fast_data_types import truncate_point_for_length, wcswidth


AGENTS = {
    "opencode": "OpenCode",
    "codex": "Codex",
    "claude": "Claude",
    "pi": "Pi",
    "agy": "Antigravity",
    "antigravity": "Antigravity",
    "antigravity-cli": "Antigravity",
}


def agent_name(cmdline):
    if not cmdline:
        return None
    path = PurePath(cmdline[0])
    if path.name in {"node", "bun"} and len(cmdline) > 1:
        path = PurePath(cmdline[1])
        if path.name == "cli.js" and path.parts[-3:-1] == ("pi-coding-agent", "dist"):
            return "Pi"
    if path.parts[-3:-1] == ("claude", "versions"):
        return "Claude"
    return AGENTS.get(path.name)


def agent_sessions(os_windows):
    # shortcut: only foreground processes are visible here, use explicit session metadata for tmux or SSH.
    for os_window in os_windows:
        for tab in os_window["tabs"]:
            for window in tab["windows"]:
                seen = set()
                for process in window.get("foreground_processes", ()):
                    agent = agent_name(process.get("cmdline", ()))
                    if agent and agent not in seen:
                        seen.add(agent)
                        yield window["id"], agent, window["title"], process.get("cwd") or window["cwd"]


def draw_session_row(screen, row, width, style, agent, title, cwd):
    title_column = 17
    cwd_column = title_column + min(42, max(14, (width - title_column) // 2))
    for column, end, value in (
        (2, title_column - 2, agent),
        (title_column, cwd_column - 2, title),
        (cwd_column, width, cwd),
    ):
        available = min(end, width) - column
        if available > 0:
            value = "".join(char if char.isprintable() else "?" for char in value)
            text = value[:truncate_point_for_length(value, available)]
            screen.addstr(row, column, text, style)


def matches_query(text, query):
    text = text.casefold()
    for word in query.casefold().split():
        chars = iter(text)
        if not all(char in chars for char in word):
            return False
    return True


def choose_session(screen, sessions):
    curses.set_escdelay(25)
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    selected = top = 0
    query = ""
    searching = False
    matches = sessions
    while True:
        height, width = screen.getmaxyx()
        framed = height >= 8 and width >= 24
        first_row = 5 if framed else 0
        visible = height - 7 if framed else height
        top = min(max(top, selected - visible + 1), selected)
        screen.erase()
        if framed:
            for row, left, right in ((0, "╭", "╮"), (2, "╰", "╯"), (3, "╭", "╮"), (height - 2, "╰", "╯")):
                screen.addstr(row, 0, left, curses.A_DIM)
                screen.hline(row, 1, "-", width - 2, curses.A_DIM)
                screen.addstr(row, width - 1, right, curses.A_DIM)
            for column in (0, width - 1):
                screen.addstr(1, column, "│", curses.A_DIM)
                for row in range(4, height - 2):
                    screen.addstr(row, column, "│", curses.A_DIM)
            prompt = f"Search: {query}" if searching else "Search (/)"
            prompt = prompt[:truncate_point_for_length(prompt, width - 4)]
            screen.addstr(1, 2, prompt, curses.A_BOLD)
            draw_session_row(screen, 4, width - 1, curses.A_DIM, "Agent", "Window title", "Working directory")
            footer = (
                "↑↓ Enter: jump   Esc: close   Ctrl+W: delete word   Ctrl+U: clear"
                if searching else "↑↓ / hjkl   Enter: jump   Esc: close"
            )
            screen.addnstr(height - 1, 0, footer, width - 1)
        if not matches:
            screen.addnstr(first_row, 1 if framed else 0, " No matching sessions", width - 2 if framed else width - 1)
        for index, (_, agent, title, cwd) in enumerate(matches[top:top + visible], top):
            row = index - top + first_row
            try:
                style = (curses.A_BOLD | curses.A_REVERSE) if index == selected else curses.A_NORMAL
                draw_session_row(screen, row, width - 1, style, agent, title, cwd)
                if index == selected:
                    left = int(framed)
                    screen.chgat(row, left, width - 1 - left, style)
                    screen.addstr(row, left, "›", style | curses.color_pair(1))
            except curses.error:
                pass
        if searching and framed:
            screen.move(1, 2 + wcswidth(prompt))
            curses.curs_set(1)
        else:
            curses.curs_set(0)
        screen.refresh()
        key = screen.get_wch()
        if key in (curses.KEY_UP, curses.KEY_LEFT) or (not searching and key in ("k", "h")):
            selected = max(0, selected - 1)
        elif key in (curses.KEY_DOWN, curses.KEY_RIGHT) or (not searching and key in ("j", "l")):
            selected = min(max(0, len(matches) - 1), selected + 1)
        elif key in ("\n", "\r", curses.KEY_ENTER):
            if matches:
                return matches[selected][0]
        elif key == "\x1b":
            return None
        elif key == "/" and not searching:
            searching = True
        elif searching:
            if key in (curses.KEY_BACKSPACE, "\b", "\x7f"):
                query = query[:-1]
            elif key == "\x17":  # Ctrl+W
                query = re.sub(r"\S*\s*$", "", query)
            elif key == "\x15":  # Ctrl+U
                query = ""
            elif isinstance(key, str) and key.isprintable():
                query += key
            else:
                continue
            matches = [session for session in sessions if matches_query(" ".join(session[1:]), query)]
            matches.sort(key=lambda session: not matches_query(session[1], query))
            selected = top = 0


def main(args):
    try:
        address = os.environ.get("KITTY_LISTEN_ON")
        if not address:
            print("Kitty remote-control socket is unavailable. Press Enter to close.")
            input()
            return None
        result = subprocess.run(
            [kitten_exe(), "@", "--to", address, "ls"],
            check=True, capture_output=True, timeout=5,
        )
        sessions = list(agent_sessions(json.loads(result.stdout)))
        if not sessions:
            input("No foreground agent sessions in Kitty. Press Enter to close.")
            return None
        # Kitty's embedded Python can start in the C locale, which breaks curses' wide-character rendering.
        locale.setlocale(locale.LC_CTYPE, "C.UTF-8")
        return curses.wrapper(choose_session, sessions)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        input("Could not read Kitty agent sessions. Press Enter to close.")
    except (EOFError, KeyboardInterrupt):
        pass
    return None


@result_handler()
def handle_result(args, answer, target_window_id, boss):
    if answer is not None and answer in boss.window_id_map:
        boss.set_active_window(answer, switch_os_window_if_needed=True)
