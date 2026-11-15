#!/bin/sh
# Link repository configs into the user's config directory.
set -eu

if [ "${1:-}" = "--help" ]; then
    echo 'Usage: ./install.sh [config ...]'
    echo 'Example: ./install.sh kitty ghostty (no arguments installs all configs)'
    exit 0
fi

case "$(uname -s)" in
Linux | Darwin) ;;
*)
    echo 'Only Linux and macOS are supported.' >&2
    exit 1
    ;;
esac

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
config_dir=${XDG_CONFIG_HOME:-"${HOME:?HOME must be set}/.config"}
case "$config_dir" in
/*) ;;
*)
    echo 'Config directory must be an absolute path.' >&2
    exit 1
    ;;
esac

if [ "$#" -eq 0 ]; then
    for source_dir in "$repo_dir"/configs/*; do
        [ -d "$source_dir" ] || continue
        set -- "$@" "${source_dir##*/}"
    done
fi

# Validate every name before changing any installed configuration.
for app; do
    case "$app" in
    '' | . | .. | */*)
        echo "Invalid config name: $app" >&2
        exit 1
        ;;
    esac
    [ -d "$repo_dir/configs/$app" ] || {
        echo "Unknown config: $app" >&2
        exit 1
    }
done

for app; do
    source_dir=$repo_dir/configs/$app
    target=$config_dir/$app

    # Keep application-managed files local; only link the managed config file.
    case "$app" in
    herdr) config_file=config.toml ;;
    bookokrat) config_file=keybindings.toml ;;
    *) config_file= ;;
    esac
    if [ -n "$config_file" ]; then
        if [ -L "$target" ] && [ "$(readlink "$target")" = "$source_dir" ]; then
            backup_dir=$(mktemp -d "$config_dir/$app.backup.XXXXXX")
            mv "$target" "$backup_dir/$app"
            mkdir -p "$target"
            cp -R "$source_dir"/. "$target"
            mv "$target/$config_file" "$backup_dir/$config_file"
            echo "Backup: $backup_dir/$app"
        elif [ -e "$target" ] && [ ! -d "$target" ]; then
            backup_dir=$(mktemp -d "$config_dir/$app.backup.XXXXXX")
            mv "$target" "$backup_dir/$app"
            echo "Backup: $backup_dir/$app"
        fi
        mkdir -p "$target"
        source_dir=$source_dir/$config_file
        target=$target/$config_file
    fi

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
