dotfiles=$HOME/dotfiles

# NOTES:
# Future idea. All subdirs could include a "sourceme" file with instructions on
# what to source in their subdirs.

# =====================
# Environment Variables
# =====================

# Remove details from terminal prompt
export PS1="$ "

# Go (brew installs `go` to /opt/homebrew/bin via shellenv above)
export GOPATH="$HOME/go"
export PATH="$PATH:$GOPATH/bin"


# Editors
export PATH="/usr/local/bin/idea:$PATH"
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

source $dotfiles/bash/aliases.sh

# =====
# MySQL
# =====

export PATH="/usr/local/opt/mysql-client/bin:$PATH"

# ==========
# PostgreSQL
# ==========

export PATH="/opt/homebrew/opt/postgresql@18/bin:$PATH"

# ======
# Python
# ======

export PATH="~/Library/Python/3.6/bin:$PATH"
export PYTHONSTARTUP="$dotfiles/.pyrc"

eval "$(pyenv init - zsh)"
#eval "$(pyenv virtualenv-init -)"  # this was slowing down the shell
			            # see https://github.com/pyenv/pyenv-virtualenv/issues/132
				    # for debug steps

# ===========
# Homebrew
# ===========
eval "$(/opt/homebrew/bin/brew shellenv)"

# ================
# Use coreutils
# (i.e. gls -> ls)
# ================
export PATH=/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH

# =========
# Misc
# =========
export PATH="$HOME/.local/bin:$PATH"
source ~/.zsh-autoenv/autoenv.zsh
