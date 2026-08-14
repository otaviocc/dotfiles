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
#   3. Symlinks every requested package from this repo into $HOME. If a
#      package has an OS-specific overlay (e.g. `git-macos`, `git-linux`),
#      that gets stowed right after it. Overlays only ever contain a
#      pre-committed relative symlink (e.g. git-macos/.gitconfig.local ->
#      ../git/.gitconfig.macos) for formats like git and Ghostty that can't
#      branch on `uname` internally but do unconditionally include a
#      "local" file. Stow creates the actual ~/.gitconfig.local symlink;
#      this script never calls `ln` itself.

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/.dotfiles-backup-$(date +%Y%m%d%H%M%S)"
OS="$(uname -s)"

case "$OS" in
  Darwin) OS_SUFFIX="macos" ;;
  Linux)  OS_SUFFIX="linux" ;;
  *)      OS_SUFFIX="" ;;
esac

ALL_PACKAGES=(zsh git nvim tmux ghostty lazygit tig herdr opencode hunk vigia)
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
    [ -e "$target" ] || continue
    # If an ancestor directory of $target is already a symlink (Stow folded
    # this subtree into the package on a previous run), $target resolves
    # straight back into $src even though the leaf itself isn't a symlink.
    # That's not a real conflict -- skip it, or we'd "back up" (i.e. delete)
    # the package's own source file out from under the repo.
    if [ "$(readlink -f -- "$target" 2>/dev/null)" = "$(readlink -f -- "$src" 2>/dev/null)" ]; then
      continue
    fi
    if [ ! -L "$target" ]; then
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

main() {
  ensure_stow

  for package in "${PACKAGES[@]}"; do
    stow_package "$package"

    overlay="${package}-${OS_SUFFIX}"
    if [ -n "$OS_SUFFIX" ] && [ -d "$DOTFILES_DIR/$overlay" ]; then
      stow_package "$overlay"
    fi
  done

  if [ -d "$BACKUP_DIR" ]; then
    log "Existing files were backed up to $BACKUP_DIR"
  fi
  log "Done."
}

main "$@"
