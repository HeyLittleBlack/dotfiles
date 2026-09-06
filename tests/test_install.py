"""Run with: python3 tests/test_install.py"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


with tempfile.TemporaryDirectory(prefix="dotfiles test ") as temporary:
    root = Path(temporary).resolve()
    repo = root / "repo with spaces"
    repo.mkdir()
    shutil.copy2(Path(__file__).resolve().parents[1] / "install.sh", repo)
    configs = repo / "configs"
    configs.mkdir()
    for app in ("kitty", "nvim", "wezterm", "ghostty", "future-app"):
        (configs / app).mkdir()
    (configs / "README.md").write_text("Not a config directory\n")
    (repo / "tests").mkdir()

    for kind in ("missing", "directory", "file", "symlink"):
        home = root / kind
        config = home / (".config" if kind == "missing" else "custom config")
        config.mkdir(parents=True)
        target = config / "kitty"
        if kind == "directory":
            target.mkdir()
            (target / "original").write_text("keep me")
        elif kind == "file":
            target.write_text("keep me")
        elif kind == "symlink":
            target.symlink_to(home / "missing target")
        nvim_target = config / "nvim"
        nvim_target.mkdir()
        (nvim_target / "init.lua").write_text("-- original config\n")

        env = dict(os.environ, HOME=str(home))
        env.pop("XDG_CONFIG_HOME", None)
        if kind != "missing":
            env["XDG_CONFIG_HOME"] = str(config)
        for _ in range(2):
            subprocess.run(["sh", str(repo / "install.sh")], cwd=root,
                           env=env, check=True, capture_output=True, text=True)
            for source in configs.iterdir():
                if source.is_dir():
                    installed = config / source.name
                    assert installed.is_symlink() and installed.resolve() == source
            assert not (config / "README.md").exists()
            assert not (config / "tests").exists()

        nvim_backups = list(config.glob("nvim.backup.*/nvim/init.lua"))
        assert len(nvim_backups) == 1
        assert nvim_backups[0].read_text() == "-- original config\n"

        backups = list(config.glob("kitty.backup.*/kitty"))
        assert len(backups) == (0 if kind == "missing" else 1)
        if kind == "directory":
            assert (backups[0] / "original").read_text() == "keep me"
        elif kind == "file":
            assert backups[0].read_text() == "keep me"
        elif kind == "symlink":
            assert backups[0].is_symlink()
            assert os.readlink(backups[0]) == str(home / "missing target")

print("Install checks passed")
