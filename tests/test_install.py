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
    for app in ("kitty", "nvim", "wezterm", "ghostty", "future-app", "herdr"):
        (configs / app).mkdir()
    (configs / "herdr/config.toml").write_text("[keys]\n")
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
            (configs / "herdr/session.json").write_text("keep my session\n")
            (config / "herdr").symlink_to(configs / "herdr")
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
                    if source.name == "herdr":
                        assert installed.is_dir() and not installed.is_symlink()
                        assert (installed / "config.toml").is_symlink()
                        assert (installed / "config.toml").resolve() == source / "config.toml"
                        if kind == "symlink":
                            assert (installed / "session.json").read_text() == "keep my session\n"
                    else:
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

    selected = root / "selected configs"
    selected.mkdir()
    (selected / "nvim").mkdir()
    (selected / "nvim/init.lua").write_text("untouched")
    env = dict(os.environ, HOME=str(root), XDG_CONFIG_HOME=str(selected))
    command = ["sh", str(repo / "install.sh")]
    for names in (("ghostty",), ("kitty", "ghostty", "kitty")):
        subprocess.run(command + list(names), cwd=root, env=env, check=True,
                       capture_output=True, text=True)
        assert set(p.name for p in selected.iterdir()) == {"nvim", *names}
        for name in names:
            assert (selected / name).is_symlink()
            assert (selected / name).resolve() == configs / name
        assert (selected / "nvim/init.lua").read_text() == "untouched"

    for invalid in ("unknown", "../tests", ".", "..", "", "README.md"):
        result = subprocess.run(command + ["wezterm", invalid], cwd=root,
                                env=env, capture_output=True, text=True)
        assert result.returncode != 0 and result.stderr
        assert not (selected / "wezterm").exists()
        assert set(p.name for p in selected.iterdir()) == {"kitty", "ghostty", "nvim"}

    result = subprocess.run(command + ["--help"], env=env, check=True,
                            capture_output=True, text=True)
    assert "Usage:" in result.stdout

print("Install checks passed")
