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
setopt SHARE_HISTORY
setopt EXTENDED_HISTORY
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS      # Remove older duplicate entries from history
setopt HIST_IGNORE_SPACE
setopt HIST_REDUCE_BLANKS        # Remove superfluous blanks from history items
setopt INC_APPEND_HISTORY        # Save history entries as soon as they are entered

# --- Options -------------------------------------------------------------

# Directory navigation
setopt AUTO_CD                   # Go to folder path without using cd
setopt AUTO_PUSHD                # Push the old directory onto the stack on cd
setopt PUSHD_IGNORE_DUPS         # Do not store duplicates in the stack
setopt PUSHD_SILENT              # Do not print the directory stack after pushd or popd

# Completion
setopt COMPLETE_IN_WORD          # Complete from both ends of a word
setopt ALWAYS_TO_END             # Move cursor to the end of a completed word
setopt AUTO_MENU                 # Show completion menu on a successive tab press
setopt AUTO_LIST                 # Automatically list choices on ambiguous completion
unsetopt MENU_COMPLETE           # Don't auto-insert first completion
setopt AUTO_PARAM_SLASH          # Add trailing slash for directory completions
setopt LIST_PACKED               # Compact completion lists

# Misc
setopt INTERACTIVE_COMMENTS      # Allow comments in interactive mode

# --- Completion ----------------------------------------------------------
autoload -Uz compinit
compinit
zstyle ':completion:*' menu select
setopt globdots  # include hidden files in TAB completion and globbing

# --- Prompt / VCS info ---------------------------------------------------
autoload -Uz vcs_info
precmd_functions+=(vcs_info)

# --- PATH ----------------------------------------------------------------
typeset -U path PATH  # de-dupe automatically, however many times we're sourced

# Add local and tool-specific bins to PATH if present
[[ -d "$HOME/.local/bin" ]] && path=("$HOME/.local/bin" $path)

# Add cargo binaries to PATH if Rust is installed
[[ -d "$HOME/.cargo/bin" ]] && path=("$HOME/.cargo/bin" $path)

# Add opencode binaries to PATH if present
[[ -d "$HOME/.opencode/bin" ]] && path=("$HOME/.opencode/bin" $path)

# --- Editor / misc ---------------------------------------------------------
if [[ -n $SSH_CONNECTION ]]; then
  export EDITOR="vim"
else
  export EDITOR="nvim"
fi

# --- Tooling ---------------------------------------------------------------
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=0
export OPENCODE_DISABLE_EXTERNAL_SKILLS=1

# --- Aliases ---------------------------------------------------------------
alias vim="nvim"
alias h="herdr"
alias g="git"
alias ..="cd .."

# ls family. Actual coloring mechanism (CLICOLOR vs --color=auto) is set up
# per-OS in .zshrc.macos / .zshrc.linux since BSD and GNU ls disagree on it;
# these flags (-l/-a/-h/-F) are portable across both.
alias ll="ls -lah"
alias l="ls -lh"
alias la="ls -a"
alias lla="ls -lhaF"

# --- Directory navigation ---------------------------------------------------

# Change to Developer directory
cdd() {
  local dev_dir="${HOME}/Developer"
  if [[ -d "${dev_dir}" ]]; then
    cd "${dev_dir}" || return 1
  else
    echo "Error: Developer directory not found at ${dev_dir}" >&2
    return 1
  fi
}

# Create directory and cd into it
mkcd() {
  mkdir -p -- "$@" && cd -- "$1" || return 1
}

# --- Utility functions -------------------------------------------------------

# Safe rm -rf with confirmation
rmf() {
  echo "About to 'rm -rf' the following:"
  for path in "$@"; do
    echo "  - ${path}"
  done

  echo -n "Are you sure? [y/N] "
  read -r confirm

  if [[ "${confirm}" == "y" || "${confirm}" == "Y" ]]; then
    command rm -rf "$@"
  else
    echo "Operation cancelled."
  fi
}

# Reload zsh configuration
reload() {
  echo -n "Are you sure you want to reload the shell? (y/n) "
  read -r confirm
  if [[ "${confirm}" == "y" ]]; then
    exec zsh
  fi
}

# --- Git functions -----------------------------------------------------------

# Sync with remote branch (stash, rebase, pop)
git-sync() {
  local branch=$(git symbolic-ref --short HEAD 2>/dev/null)
  if [[ -z "${branch}" ]]; then
    echo "Error: Not in a git repository" >&2
    return 1
  fi

  local stash_name="sync-stash-$(date +%Y%m%d-%H%M%S)"

  echo "Creating stash: ${stash_name}"

  # Attempt to stash - capture if anything was actually stashed
  local stash_output=$(git stash push -m "${stash_name}" 2>&1)
  local stash_created=false

  if [[ ! "${stash_output}" =~ "No local changes to save" ]]; then
    stash_created=true
    echo "Stash created successfully"
  else
    echo "No changes to stash"
  fi

  if git fetch && git rebase origin/${branch}; then
    # Only pop if we actually created a stash
    if [[ "${stash_created}" == "true" ]]; then
      echo "Popping stash: ${stash_name}"
      git stash pop
    fi
  else
    if [[ "${stash_created}" == "true" ]]; then
      echo "Rebase failed - your changes are safely in stash: ${stash_name}"
    else
      echo "Rebase failed - no stash was created"
    fi
    return 1
  fi
}

# Change author of a specific git commit
git-change-author() {
  if ! command -v perl &> /dev/null; then
    echo "Error: perl is not installed. Please install it to use this function." >&2
    return 1
  fi

  # Check argument count
  if [[ $# -ne 2 ]]; then
    echo "Usage: git-change-author <author> <commit>" >&2
    return 1
  fi

  local author="$1"
  local author_name=$(echo "${author}" | perl -wlne '/^(.*?)\s*<.*>$/ and print $1')
  local author_email=$(echo "${author}" | perl -wlne '/^.*\s*<(.*)>$/ and print $1')
  local commit=$(git rev-parse --short "$2" 2>/dev/null)

  # Check if commit exists
  if [[ $? -ne 0 ]]; then
    echo "Error: Invalid commit '$2'" >&2
    return 1
  fi

  # Perform the rebase operation. sed's in-place flag differs between BSD
  # (macOS, needs an empty suffix arg) and GNU (Linux, no suffix arg).
  local sed_inplace
  if sed --version >/dev/null 2>&1; then
    sed_inplace="sed -i"          # GNU sed
  else
    sed_inplace="sed -i ''"       # BSD sed (macOS)
  fi

  {
    GIT_SEQUENCE_EDITOR="${sed_inplace} \"s/^pick ${commit}/edit ${commit}/\"" git rebase -i ${commit}~1^^ && \
    GIT_COMMITTER_NAME="${author_name}" GIT_COMMITTER_EMAIL="${author_email}" git commit --amend --no-edit --author="${author}" && \
    git rebase --continue
  } &> /dev/null

  if [[ $? -eq 0 ]]; then
    echo "${author_name} is now the author of ${commit}. You're officially an asshole."
  else
    echo "Error: Failed to change commit author. Repository may be in an inconsistent state." >&2
    return 1
  fi
}

# --- Key bindings --------------------------------------------------------

bindkey -e

# History search with arrow keys
autoload -U up-line-or-beginning-search
autoload -U down-line-or-beginning-search
zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search
bindkey "^[[A" up-line-or-beginning-search
bindkey "^[[B" down-line-or-beginning-search

# Home / End / Delete
bindkey '^[[H' beginning-of-line
bindkey '^[[F' end-of-line
bindkey '^[[3~' delete-char

# --- Kanagawa Dragon theme (colors, prompt, LS_COLORS) --------------------
# Palette: bg #181616, bg_m3 #0d0c0c, fg #c5c9c5, comment #737c73,
# yellow #c4b28a (accent), orange #b6927b, red #c4746e, violet #8992a7.
# The full table lives in docs/palette.md.
# Upstream: https://github.com/rebelot/kanagawa.nvim
#
# `ls` colors. Two variables, because the two `ls` implementations disagree:
#
#   LS_COLORS  GNU ls, eza, fd, zsh completion. Truecolor, 677 rules,
#              vendored in .config/zsh/ls_colors.zsh. vivid has no Kanagawa,
#              so that file is vivid's gruvbox-dark output with the palette
#              remapped to Dragon — see its header.
#   LSCOLORS   BSD /bin/ls only, and it ignores LS_COLORS entirely. 8 ANSI
#              colours, no per-extension rules — it can't express the palette,
#              it just picks slots the terminal theme has already coloured.
#
# macOS aliases ls -> gls (see .zshrc.macos) so the truecolor set is what you
# actually see on both machines; LSCOLORS is only the fallback for an explicit
# /bin/ls. Its slot order is dir, symlink, socket, pipe, executable, block,
# char, setuid, setgid, sticky-dir, other-writable-dir — kept in step with the
# remapped set: warm-yellow dirs, blue links, pink sockets and pipes, green
# executables.
export CLICOLOR=YES
export LSCOLORS="DxExFxFxCxEgEdAbAgAcAd"
[ -r "$HOME/.config/zsh/ls_colors.zsh" ] && source "$HOME/.config/zsh/ls_colors.zsh"

# Completion list colors (uses LS_COLORS above)
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*:descriptions' format '%F{#8992a7}-- %d --%f'

# VCS / prompt colors
zstyle ':vcs_info:git:*' formats '%F{#c4b28a}%b%f '

setopt PROMPT_SUBST
PROMPT=$'%F{#8992a7}%~%f ${vcs_info_msg_0_}\n%F{#737c73}$%f '

# --- GPG -----------------------------------------------------------------
export GPG_TTY=$(tty)

# --- fzf ------------------------------------------------------------------
source <(fzf --zsh)

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
