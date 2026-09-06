#!/bin/sh
# Link repository configs into the user's config directory.
set -eu

case "$(uname -s)" in
    Linux|Darwin) ;;
    *) echo 'Only Linux and macOS are supported.' >&2; exit 1 ;;
esac

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
config_dir=${XDG_CONFIG_HOME:-"${HOME:?HOME must be set}/.config"}
case "$config_dir" in
    /*) ;;
    *) echo 'Config directory must be an absolute path.' >&2; exit 1 ;;
esac

for app in kitty nvim; do
    source_dir=$repo_dir/$app
    target=$config_dir/$app
    [ -d "$source_dir" ] || { echo "Missing config: $source_dir" >&2; exit 1; }

    if [ -L "$target" ] && [ "$(readlink "$target")" = "$source_dir" ]; then
        echo "Already installed: $target"
        continue
    fi

    mkdir -p "$config_dir"
    if [ -e "$target" ] || [ -L "$target" ]; then
        backup_dir=$(mktemp -d "$config_dir/$app.backup.XXXXXX")
        mv "$target" "$backup_dir/$app"
        echo "Backup: $backup_dir/$app"
    fi

    ln -s "$source_dir" "$target"
    echo "Installed: $target -> $source_dir"
done
