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

ALL_PACKAGES=(zsh git nvim tmux ghostty sublime lazygit tig yazi herdr opencode hunk vigia bat claude holodeck vademecum)

# Packages with no Linux counterpart at all. These are ordinary packages, not
# the `*-macos` symlink overlays: `sublime` exists on both machines and only
# its *path* differs, whereas Xcode simply does not exist on Fedora, so
# stowing it there would create an empty ~/Library/Developer tree. They are
# appended to the default set on Darwin and skipped with a note on Linux,
# including when named explicitly.
DARWIN_ONLY_PACKAGES=(xcode)
if [ "$OS_SUFFIX" = "macos" ]; then
  ALL_PACKAGES+=("${DARWIN_ONLY_PACKAGES[@]}")
fi

PACKAGES=("${@:-${ALL_PACKAGES[@]}}")

log() { printf '==> %s\n' "$1"; }

is_darwin_only() {
  local p
  for p in "${DARWIN_ONLY_PACKAGES[@]}"; do
    [ "$p" = "$1" ] && return 0
  done
  return 1
}

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
backup_target() {
  local rel="$1" target="$2" what="file"
  # A package entry can be a directory symlink (sublime-macos points its whole
  # Packages/User at the base package), so the thing being moved aside is
  # sometimes a populated directory. Say so -- it is a much bigger move than a
  # single file, and the log is the only warning before it happens.
  [ -L "$target" ] || { [ -d "$target" ] && what="directory"; }
  mkdir -p "$BACKUP_DIR/$(dirname "$rel")"
  log "Backing up existing $what ~/$rel -> $BACKUP_DIR/$rel"
  mv "$target" "$BACKUP_DIR/$rel"
}

backup_conflicts() {
  local package="$1"
  local pkg_dir="$DOTFILES_DIR/$package"
  [ -d "$pkg_dir" ] || return 0

  local src rel target link resolved
  while IFS= read -r -d '' src; do
    rel="${src#"$pkg_dir"/}"
    target="$HOME/$rel"
    # -e alone is false for a dangling symlink, which is very much a conflict.
    [ -e "$target" ] || [ -L "$target" ] || continue

    if [ ! -L "$target" ]; then
      # A real file. It may still be the package's own file seen through a
      # directory symlink an earlier run folded into place, in which case
      # $target resolves straight back to $src -- backing that up would delete
      # the source out from under the repo.
      if [ "$(readlink -f -- "$target" 2>/dev/null)" = "$(readlink -f -- "$src" 2>/dev/null)" ]; then
        continue
      fi
      backup_target "$rel" "$target"
      continue
    fi

    # A symlink. Stow only owns *relative* links pointing inside the stow dir;
    # it refuses anything else ("Ignoring an absolute symlink" / "existing
    # target is not owned by stow") and aborts the whole run. Note that an
    # absolute link can resolve to exactly the right file and still abort the
    # run, so where it points is not the question -- how it points is.
    link="$(readlink -- "$target")"
    resolved="$(readlink -f -- "$target" 2>/dev/null || true)"
    case "$link" in
      /*) backup_target "$rel" "$target" ;;
      *)
        case "$resolved" in
          "$DOTFILES_DIR"/*) : ;;
          *) backup_target "$rel" "$target" ;;
        esac
        ;;
    esac
  # -type l matters: the OS-overlay packages (git-macos, ghostty-macos, ...)
  # are made *entirely* of pre-committed relative symlinks, which a bare
  # -type f scan walks straight past, so their conflicts went undetected.
  done < <(find "$pkg_dir" \( -type f -o -type l \) ! -name .DS_Store -print0)
}

stow_package() {
  local package="$1"
  [ -d "$DOTFILES_DIR/$package" ] || { echo "Unknown package: $package" >&2; return 1; }
  backup_conflicts "$package"
  log "Stowing $package"
  # Finder scatters .DS_Store inside the packages. They are gitignored, so they
  # never surface in `git status`, but stow would cheerfully symlink them into
  # $HOME on top of the real ones.
  stow -d "$DOTFILES_DIR" -t "$HOME" --ignore='\.DS_Store' -R "$package"
}

main() {
  ensure_stow

  for package in "${PACKAGES[@]}"; do
    if [ "$OS_SUFFIX" != "macos" ] && is_darwin_only "$package"; then
      log "Skipping $package (macOS only)"
      continue
    fi
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
