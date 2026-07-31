#!/usr/bin/env bash
#
# Bootstrap script for ~/.dotfiles.
#
# Usage:
#   ./install.sh                 # stow every package
#   ./install.sh zsh git nvim    # stow only the given packages
#
# What it does:
#   1. Makes sure GNU Stow is installed (dnf on Fedora, brew on macOS).
#   2. Backs up any real (non-symlink) files/dirs that would collide with a
#      package, so `stow` can safely take over.
#   3. Symlinks every requested package from this repo into $HOME.
#   4. Wires up the OS-specific "local include" files that formats like git
#      and Ghostty can't branch on internally (git/.gitconfig.local,
#      ghostty config.local).
#   5. On macOS, symlinks VS Code settings into
#      "~/Library/Application Support/Code/User" separately, since that path
#      is completely different from the Linux/XDG one and Stow only supports
#      a single target directory per invocation.

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/.dotfiles-backup-$(date +%Y%m%d%H%M%S)"
OS="$(uname -s)"

ALL_PACKAGES=(zsh git nvim tmux ghostty lazygit tig herdr opencode vscode)
PACKAGES=("${@:-${ALL_PACKAGES[@]}}")

log() { printf '==> %s\n' "$1"; }

ensure_stow() {
  if command -v stow >/dev/null 2>&1; then
    return
  fi
  log "Installing GNU Stow..."
  if [ "$OS" = "Darwin" ]; then
    brew install stow
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y stow
  else
    echo "Don't know how to install stow on this system. Install it manually." >&2
    exit 1
  fi
}

# Move any real file/dir that a package would try to symlink over into
# $BACKUP_DIR, preserving the relative path, so stow doesn't refuse to link.
backup_conflicts() {
  local package="$1"
  local pkg_dir="$DOTFILES_DIR/$package"
  [ -d "$pkg_dir" ] || return 0

  while IFS= read -r -d '' src; do
    local rel="${src#"$pkg_dir"/}"
    local target="$HOME/$rel"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
      mkdir -p "$BACKUP_DIR/$(dirname "$rel")"
      log "Backing up existing ~/$rel -> $BACKUP_DIR/$rel"
      mv "$target" "$BACKUP_DIR/$rel"
    fi
  done < <(find "$pkg_dir" -type f -print0)
}

stow_package() {
  local package="$1"
  [ -d "$DOTFILES_DIR/$package" ] || { echo "Unknown package: $package" >&2; return 1; }
  backup_conflicts "$package"
  log "Stowing $package"
  stow -d "$DOTFILES_DIR" -t "$HOME" -R "$package"
}

setup_git_local_include() {
  local target
  case "$OS" in
    Darwin) target="$DOTFILES_DIR/git/.gitconfig.macos" ;;
    Linux)  target="$DOTFILES_DIR/git/.gitconfig.linux" ;;
    *) echo "Unsupported OS for git local include: $OS" >&2; return 0 ;;
  esac
  log "Linking ~/.gitconfig.local -> $target"
  ln -sfn "$target" "$HOME/.gitconfig.local"
}

setup_ghostty_local_include() {
  [ -d "$HOME/.config/ghostty" ] || return 0
  local target
  case "$OS" in
    Darwin) target="$DOTFILES_DIR/ghostty/.config/ghostty/config.macos" ;;
    Linux)  target="$DOTFILES_DIR/ghostty/.config/ghostty/config.linux" ;;
    *) return 0 ;;
  esac
  log "Linking ~/.config/ghostty/config.local -> $target"
  ln -sfn "$target" "$HOME/.config/ghostty/config.local"
}

setup_vscode_macos() {
  [ "$OS" = "Darwin" ] || return 0
  local target_dir="$HOME/Library/Application Support/Code/User"
  mkdir -p "$target_dir"
  log "Linking VS Code settings into $target_dir (macOS path differs from Linux)"
  ln -sfn "$DOTFILES_DIR/vscode/.config/Code/User/settings.json" "$target_dir/settings.json"
}

main() {
  ensure_stow
  mkdir -p "$HOME/.config"

  for package in "${PACKAGES[@]}"; do
    if [ "$package" = "vscode" ] && [ "$OS" = "Darwin" ]; then
      setup_vscode_macos
      continue
    fi
    stow_package "$package"
  done

  if printf '%s\n' "${PACKAGES[@]}" | grep -qx git; then
    setup_git_local_include
  fi
  if printf '%s\n' "${PACKAGES[@]}" | grep -qx ghostty; then
    setup_ghostty_local_include
  fi

  if [ -d "$BACKUP_DIR" ]; then
    log "Existing files were backed up to $BACKUP_DIR"
  fi
  log "Done."
}

main "$@"
