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
alias ll="ls -lah"
alias g="git"

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
