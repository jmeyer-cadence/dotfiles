dotfiles=$HOME/dotfiles

# NOTES:
# Future idea. All subdirs could include a "sourceme" file with instructions on
# what to source in their subdirs.

# ===========
# Homebrew
# ===========

if [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
elif [ -x /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
fi

# Keep the path array de-duplicated; zsh keeps PATH and path in sync.
typeset -U path PATH

# =====================
# Environment Variables
# =====================

# Remove details from terminal prompt
export PS1="$ "

# Go (brew installs `go` to /opt/homebrew/bin via shellenv above)
export GOPATH="$HOME/go"
path+=("$GOPATH/bin")


# Editors
path=("/usr/local/bin/idea" $path)
export EDITOR=vim

# =====================
# Enable vi keybindings
# =====================

set -o vi

# =================
# Track cmd history
# =================

# Maximum number of history lines in memory
export HISTSIZE=50000

# Maximum number of history lines on disk
export HISTFILESIZE=50000

# Share history between sessions
setopt share_history

# Ignore duplicates in history
setopt hist_ignore_dups

# Append new history entries without overwriting existing ones
setopt append_history

# Manually bind lookback key
bindkey "^R" history-incremental-search-backward

# =============
# ENV Variables
# =============

# TODO recursively source files in env/

# ========
# RC Files
# ========

# .ideavimrc should not be sourced
#for f in "$dotfiles/rc/.[^.]*"; do source $f; done

# ==============
# Alias handling
# ==============

source "$dotfiles/bash/aliases.sh"

# =====
# MySQL
# =====

path=("/usr/local/opt/mysql-client/bin" $path)

# ==========
# PostgreSQL
# ==========

path=("/opt/homebrew/opt/postgresql@18/bin" $path)

# ======
# Python
# ======

path+=("$HOME/Library/Python/3.6/bin")
export PYTHONSTARTUP="$dotfiles/.pyrc"

if command -v pyenv >/dev/null 2>&1; then
    eval "$(pyenv init - --no-rehash zsh)"
fi
#eval "$(pyenv virtualenv-init -)"  # this was slowing down the shell
                                # see https://github.com/pyenv/pyenv-virtualenv/issues/132
                            # for debug steps

# ================
# Use coreutils
# (i.e. gls -> ls)
# ================
if [ -d /opt/homebrew/opt/coreutils/libexec/gnubin ]; then
    path=(/opt/homebrew/opt/coreutils/libexec/gnubin $path)
fi

# =====================
# Enable zsh completion
# =====================

autoload -Uz compinit
compinit

# =========
# Misc
# =========
path=("$HOME/.local/bin" $path)
export PATH

# ================
# Shell completions
# ================

if command -v workmux >/dev/null 2>&1; then
    eval "$(workmux completions zsh)"

    _workmux_handles() {
        local -a handles
        handles=(${${(f)"$(git worktree list --porcelain 2>/dev/null | awk '/^worktree/{print $2}')"}[2,-1]:t})
        compadd -a handles
    }
fi

if [ -f "$HOME/.zshrc.work" ]; then
    source "$HOME/.zshrc.work"
elif [ -f "$HOME/.zsh-autoenv/autoenv.zsh" ]; then
    # Backward-compatible fallback until work-only shell settings live in ~/.zshrc.work.
    source "$HOME/.zsh-autoenv/autoenv.zsh"
fi
