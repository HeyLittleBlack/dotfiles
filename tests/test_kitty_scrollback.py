"""Run with: python3 tests/test_kitty_scrollback.py (requires Vim +terminal)."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile

config = Path(__file__).resolve().parents[1] / "configs/kitty/kitty.conf"
line = next(line for line in config.read_text().splitlines() if line.startswith("scrollback_pager "))
arguments = shlex.split(line)[1:]
commands = [arguments[i + 1] for i, arg in enumerate(arguments) if arg == "-c"]

with tempfile.TemporaryDirectory() as directory:
    check = Path(directory) / "check.vim"
    capture = Path(directory) / "captured"
    cat = Path(directory) / "cat"
    cat.write_text('#!/bin/sh\nset -e\ncp "$1" "$SCROLLBACK_TEST_CAPTURE"\nexec /bin/cat "$@"\n')
    cat.chmod(0o755)
    check.write_text("\n".join([
        'call setline(1, ["scrollback-check", "\x1b[31mred-text\x1b[0m"])',
        *commands,
        'let terminal = bufnr("%")',
        'for attempt in range(100)',
        '  call term_wait(terminal, 20)',
        '  if job_status(term_getjob(terminal)) ==# "dead" && !filereadable(g:scrollback_file) | break | endif',
        'endfor',
        'call assert_equal(0, job_info(term_getjob(terminal)).exitval)',
        'call assert_equal(0, filereadable(g:scrollback_file))',
        'if !empty(v:errors) | echo v:errors | cquit | endif',
        'qa!',
    ]) + "\n")
    subprocess.run(["vim", "-u", "NORC", "-i", "NONE", "-n", "-es", "-S", str(check)],
                   check=True, timeout=10,
                   env=dict(os.environ, PATH=directory + os.pathsep + os.environ["PATH"],
                            SCROLLBACK_TEST_CAPTURE=str(capture)))
    assert capture.read_bytes() == b"scrollback-check\n\x1b[31mred-text\x1b[0m\n"

print("Vim scrollback check passed")
