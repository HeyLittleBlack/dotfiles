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

source_dir=$repo_dir/kitty
target=$config_dir/kitty
[ -d "$source_dir" ] || { echo "Missing config: $source_dir" >&2; exit 1; }

if [ -L "$target" ] && [ "$(readlink "$target")" = "$source_dir" ]; then
    echo "Already installed: $target"
    exit 0
fi

mkdir -p "$config_dir"
if [ -e "$target" ] || [ -L "$target" ]; then
    backup_dir=$(mktemp -d "$config_dir/kitty.backup.XXXXXX")
    mv "$target" "$backup_dir/kitty"
    echo "Backup: $backup_dir/kitty"
fi

ln -s "$source_dir" "$target"
echo "Installed: $target -> $source_dir"
