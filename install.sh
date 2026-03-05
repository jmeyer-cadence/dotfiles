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

# ====================
# Package managers
# ====================

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

if [ -x "$(command -v npm)" ]; then
    success "npm already installed"
elif ask "npm not found. Install it? (via node)"; then
    starting "install node"
    brew install node
    success "node/npm installed"
else
    skipping "npm"
fi

# ================
# Install packages
# ================

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

if [ -x "$(command -v go)" ]; then
    success "go already installed"
elif ask "go not found. Install it?"; then
    starting "install go"
    brew install go
    success "go installed"
else
    skipping "go"
fi

if brew list postgresql@18 &>/dev/null; then
    success "postgresql already installed"
elif ask "postgresql not found. Install it? (provides psql)"; then
    starting "install postgresql"
    brew install postgresql@18
    success "postgresql installed"
else
    skipping "postgresql"
fi

if brew list --cask hammerspoon &>/dev/null; then
    success "hammerspoon already installed"
elif ask "Hammerspoon not found. Install it? (window manager)"; then
    starting "install hammerspoon"
    brew install --cask hammerspoon
    success "hammerspoon installed"
else
    skipping "hammerspoon"
fi

if [ -d "/Applications/Karabiner-Elements.app" ]; then
    if pgrep -qf "Karabiner-Elements"; then
        success "karabiner-elements installed and running"
    else
        warning "karabiner-elements installed but not running — open it from /Applications"
    fi
else
    warning "karabiner-elements not installed — download from https://karabiner-elements.pqrs.org"
fi


# ======================
# Work git identity stub
# ======================

if [ -f "$HOME/.gitconfig-work" ]; then
    success "~/.gitconfig-work already exists"
else
    cat > "$HOME/.gitconfig-work" <<'EOF'
[user]
	name = your-work-name
	email = your-work-email@example.com
EOF
    warning "Created stub ~/.gitconfig-work — update it with your work identity"
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

mkdir -p "$HOME/.hammerspoon"
link_file "$DOTFILES/hammerspoon/init.lua"          "$HOME/.hammerspoon/init.lua"

mkdir -p "$HOME/.config/karabiner"
karabiner_src="$DOTFILES/karabiner/karabiner.json"
karabiner_dest="$HOME/.config/karabiner/karabiner.json"
if [ ! -f "$karabiner_dest" ]; then
    cp "$karabiner_src" "$karabiner_dest" && echo "  🔗 Copied: $karabiner_dest"
elif diff -q "$karabiner_src" "$karabiner_dest" &>/dev/null; then
    success "karabiner config up to date"
elif ask "karabiner config differs from dotfiles. Replace $karabiner_dest with dotfiles version?"; then
    cp "$karabiner_src" "$karabiner_dest" && success "karabiner config updated"
else
    skipping "karabiner config"
fi


# ========
# Complete
# ========

success "setup complete!"

echo ""
echo "  Open a new terminal (or run 'source ~/.zshrc' in zsh) to apply changes."
echo ""
