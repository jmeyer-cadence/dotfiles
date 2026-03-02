#!/bin/bash

DOTFILES="$HOME/dotfiles"

GREEN=$'\033[32m'
YELLOW=$'\033[33m'
RED=$'\033[31m'
RESET=$'\033[0m'

# Output helpers

function starting() {
    echo "▶️  Starting: $1"
}

function success() {
    echo "✅  ${GREEN}SUCCESS: $1${RESET}"
}

function failure() {
    echo "❌  ${RED}FAIL: $1${RESET}"
}

function warning() {
    echo "⚠️   ${YELLOW}WARN: $1${RESET}"
}

function skipping() {
    echo " ⏭️   Skipping $1"
}

function ask() {
    read -r -p "  ❓ $1 [y/N] " response
    [[ "$response" =~ ^[Yy]$ ]]
}

function link_file() {
    local src="$1"
    local dest="$2"
    if [ -L "$dest" ]; then
        success "$dest already symlinked"
    elif [ -e "$dest" ]; then
        warning "$dest exists but is not a symlink — remove it manually to replace"
    else
        ln -s "$src" "$dest" && echo "  🔗 Linked: $dest -> $src"
    fi
}

# ================
# Install packages
# ================

if [ -x "$(command -v brew)" ]; then
    success "brew already installed"
elif ask "Homebrew not found. Install it?"; then
    starting "install brew"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$(/opt/homebrew/bin/brew shellenv)"
    success "brew installed"
else
    skipping "brew"
fi

if [ -x "$(command -v gls)" ]; then
    success "coreutils already installed"
elif ask "coreutils not found. Install it?"; then
    starting "install coreutils"
    brew install coreutils
    success "coreutils installed"
else
    skipping "coreutils"
fi

if [ -x "$(command -v pyenv)" ]; then
    success "pyenv already installed"
elif ask "pyenv not found. Install it?"; then
    starting "install pyenv"
    brew install pyenv
    success "pyenv installed"
else
    skipping "pyenv"
fi

if [ -x "$(command -v tmux)" ]; then
    success "tmux already installed"
elif ask "tmux not found. Install it?"; then
    starting "install tmux"
    brew install tmux
    success "tmux installed"
else
    skipping "tmux"
fi

if [ -x "$(command -v workmux)" ]; then
    success "workmux already installed"
elif ask "workmux not found. Install it?"; then
    starting "install workmux"
    brew install raine/workmux/workmux
    success "workmux installed"
else
    skipping "workmux"
fi

if [ -x "$(command -v difit)" ]; then
    success "difit already installed"
elif ask "difit not found. Install it? (requires npm)"; then
    starting "install difit"
    npm install -g difit
    success "difit installed"
else
    skipping "difit"
fi


# =============
# Link dotfiles
# =============

starting "linking dotfiles"

link_file "$DOTFILES/.zshrc"            "$HOME/.zshrc"
link_file "$DOTFILES/.gitconfig"        "$HOME/.gitconfig"
link_file "$DOTFILES/.gitignore_global" "$HOME/.gitignore_global"
link_file "$DOTFILES/.inputrc"          "$HOME/.inputrc"
link_file "$DOTFILES/.pyrc"             "$HOME/.pyrc"
link_file "$DOTFILES/.tmux.conf"        "$HOME/.tmux.conf"
link_file "$DOTFILES/.claude/CLAUDE.md"  "$HOME/.claude/CLAUDE.md"
link_file "$DOTFILES/.claude/hooks"      "$HOME/.claude/hooks"


# ========
# Complete
# ========

success "setup complete!"

echo ""
echo "  Open a new terminal (or run 'source ~/.zshrc' in zsh) to apply changes."
echo ""
