# ~/.zshrc — plain zsh, no framework (oh-my-zsh removed 2026-07-31).
#
# Layout:
#   - shared settings for every machine live directly in this file
#   - OS-specific bits live in .zshrc.linux / .zshrc.macos (both tracked in
#     this repo, picked automatically at runtime based on `uname`)
#   - anything truly private/one-off for a single machine can go in
#     ~/.zshrc.local (NOT tracked, sourced last if present)

# --- History -----------------------------------------------------------
HISTFILE="$HOME/.zsh_history"
HISTSIZE=50000
SAVEHIST=50000
setopt APPEND_HISTORY
setopt SHARE_HISTORY
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_SPACE

# --- Completion ----------------------------------------------------------
autoload -Uz compinit
compinit
zstyle ':completion:*' menu select

# --- Prompt / VCS info ---------------------------------------------------
autoload -Uz vcs_info
precmd_functions+=(vcs_info)

# --- PATH ----------------------------------------------------------------
typeset -U path PATH  # de-dupe automatically, however many times we're sourced
path=("$HOME/.local/bin" "$HOME/.opencode/bin" $path)

# --- Editor / misc ---------------------------------------------------------
export EDITOR="nvim"

# --- Aliases ---------------------------------------------------------------
alias vim="nvim"
alias h="herdr"
alias ll="ls -lah"
alias g="git"

# --- Default+ theme (colors, prompt, LS_COLORS) --------------------------
# Vendored from https://github.com/otaviocc/default-plus (see README for
# how to re-sync if the palette changes upstream).
[ -f "$HOME/.zsh_default-plus.zsh" ] && source "$HOME/.zsh_default-plus.zsh"

# --- OS-specific config ---------------------------------------------------
case "$(uname -s)" in
  Darwin)
    [ -f "$HOME/.zshrc.macos" ] && source "$HOME/.zshrc.macos"
    ;;
  Linux)
    [ -f "$HOME/.zshrc.linux" ] && source "$HOME/.zshrc.linux"
    ;;
esac

# --- Local, untracked, machine-only overrides ------------------------------
[ -f "$HOME/.zshrc.local" ] && source "$HOME/.zshrc.local"
