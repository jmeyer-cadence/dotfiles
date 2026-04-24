#!/bin/bash

DOTFILES="$HOME/dotfiles"

GREEN=$'\033[32m'
YELLOW=$'\033[33m'
RED=$'\033[31m'
RESET=$'\033[0m'

_INDENT=""

# Output helpers

function starting() {
    echo ""
    echo "▶️  $1"
    _INDENT="  │  "
}

function success() {
    echo "${_INDENT}✅  ${GREEN}$1${RESET}"
}

function failure() {
    echo "${_INDENT}❌  ${RED}$1${RESET}"
}

function warning() {
    echo "${_INDENT}⚠️   ${YELLOW}$1${RESET}"
}

function complete() {
    echo "${_INDENT}🏁  ${GREEN}$1${RESET}"
}

function skipping() {
    echo "${_INDENT}⏭️   Skipping $1"
}

function ask() {
    read -r -p "${_INDENT}❓ $1 [y/N] " response
    [[ "$response" =~ ^[Yy]$ ]]
}

function diff_files() {
    local src="$1"
    local dest="$2"
    local src_label="${3:-$src}"
    local dest_label="${4:-$dest}"
    if [ -x "$(command -v git)" ]; then
        git diff --no-index --src-prefix="$src_label: " --dst-prefix="$dest_label: " "$src" "$dest"; true
    else
        diff "$src" "$dest"
    fi
}

function canonical_path() {
    python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"
}

function link_file() {
    local src="$1"
    local dest="$2"
    local src_display="${src/#$HOME/~}"
    local dest_display="${dest/#$HOME/~}"
    local src_canonical
    local dest_canonical
    local current_link

    mkdir -p "$(dirname "$dest")"
    src_canonical="$(canonical_path "$src")"

    if [ -L "$dest" ]; then
        dest_canonical="$(canonical_path "$dest")"
        if [ "$src_canonical" = "$dest_canonical" ]; then
            success "$dest_display already symlinked"
        else
            current_link="$(readlink "$dest")"
            warning "$dest_display points to ${current_link/#$HOME/~}"
            if ask "Replace the symlink for $dest_display?"; then
                rm "$dest" && ln -s "$src" "$dest" && success "updated symlink for $dest_display"
            else
                skipping "$dest_display"
            fi
        fi
    elif [ -e "$dest" ]; then
        warning "$dest_display exists but is not a symlink — remove it manually to replace"
    else
        ln -s "$src" "$dest" && echo "${_INDENT}🔗 Linked: $dest_display -> $src_display"
    fi
}

function link_file_with_backup() {
    local src="$1"
    local dest="$2"
    local src_display="${src/#$HOME/~}"
    local dest_display="${dest/#$HOME/~}"
    local src_canonical
    local dest_canonical
    local current_link
    local backup

    mkdir -p "$(dirname "$dest")"
    src_canonical="$(canonical_path "$src")"

    if [ -L "$dest" ]; then
        dest_canonical="$(canonical_path "$dest")"
        if [ "$src_canonical" = "$dest_canonical" ]; then
            success "$dest_display already symlinked"
        else
            current_link="$(readlink "$dest")"
            warning "$dest_display points to ${current_link/#$HOME/~}"
            if ask "Replace the symlink for $dest_display?"; then
                rm "$dest" && ln -s "$src" "$dest" && success "updated symlink for $dest_display"
            else
                skipping "$dest_display"
            fi
        fi
    elif [ -e "$dest" ]; then
        if cmp -s "$src" "$dest"; then
            rm "$dest" && ln -s "$src" "$dest" && success "replaced matching file with symlink for $dest_display"
        else
            warning "$dest_display exists but is not a symlink"
            diff_files "$src" "$dest" "$src_display" "$dest_display"
            if ask "Back up and replace $dest_display with a symlink?"; then
                backup="$dest.backup.$(date +%Y%m%d%H%M%S)"
                mv "$dest" "$backup" && ln -s "$src" "$dest" && success "backed up $dest_display to ${backup/#$HOME/~} and linked it"
            else
                skipping "$dest_display"
            fi
        fi
    else
        ln -s "$src" "$dest" && echo "${_INDENT}🔗 Linked: $dest_display -> $src_display"
    fi
}

# =======================
# Xcode Command Line Tools
# =======================

starting "Xcode Command Line Tools"

if xcode-select -p &>/dev/null; then
    success "Xcode Command Line Tools already installed"
elif ask "Xcode Command Line Tools not found. Install it?"; then
    xcode-select --install
    success "Xcode Command Line Tools installed"
else
    skipping "Xcode Command Line Tools"
fi

# ====================
# Package managers
# ====================

starting "Package managers"

if [ -x "$(command -v brew)" ]; then
    success "brew already installed"
elif ask "Homebrew not found. Install it?"; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$(/opt/homebrew/bin/brew shellenv)"
    success "brew installed"
else
    skipping "brew"
fi

if [ -x "$(command -v npm)" ]; then
    success "npm already installed"
elif ask "npm not found. Install it? (via node)"; then
    brew install node
    success "node/npm installed"
else
    skipping "npm"
fi

# ================
# Install packages
# ================

starting "Install packages"

if [ -x "$(command -v gls)" ]; then
    success "coreutils already installed"
elif ask "coreutils not found. Install it?"; then
    brew install coreutils
    success "coreutils installed"
else
    skipping "coreutils"
fi

if [ -x "$(command -v pyenv)" ]; then
    success "pyenv already installed"
elif ask "pyenv not found. Install it?"; then
    brew install pyenv
    success "pyenv installed"
else
    skipping "pyenv"
fi

if [ -x "$(command -v tmux)" ]; then
    success "tmux already installed"
elif ask "tmux not found. Install it?"; then
    brew install tmux
    success "tmux installed"
else
    skipping "tmux"
fi

if [ -d "$HOME/.tmux/plugins/tpm" ]; then
    success "tpm (tmux plugin manager) already installed"
elif ask "tpm not found. Install it?"; then
    git clone https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"
    success "tpm installed"
else
    skipping "tpm"
fi

if [ -x "$(command -v workmux)" ]; then
    success "workmux already installed"
elif ask "workmux not found. Install it?"; then
    brew install raine/workmux/workmux
    success "workmux installed"
else
    skipping "workmux"
fi

if [ -x "$(command -v difit)" ]; then
    success "difit already installed"
elif ask "difit not found. Install it? (requires npm)"; then
    npm install -g difit
    success "difit installed"
else
    skipping "difit"
fi

if [ -x "$(command -v terminal-notifier)" ]; then
    success "terminal-notifier already installed"
elif ask "terminal-notifier not found. Install it? (optional: Claude hooks and Codex notifications use it for richer macOS banners; without it, notifications fall back to the native macOS banner with no custom click action)"; then
    brew install terminal-notifier
    success "terminal-notifier installed"
else
    skipping "terminal-notifier"
fi

if [ -x "$(command -v go)" ]; then
    success "go already installed"
elif ask "go not found. Install it?"; then
    brew install go
    success "go installed"
else
    skipping "go"
fi

if [ -x "$(command -v gcloud)" ]; then
    success "gcloud already installed"
elif ask "gcloud not found. Install it?"; then
    brew install --cask gcloud-cli
    success "gcloud installed"
else
    skipping "gcloud"
fi

if brew list postgresql@18 &>/dev/null; then
    success "postgresql already installed"
elif ask "postgresql not found. Install it? (provides psql)"; then
    brew install postgresql@18
    success "postgresql installed"
else
    skipping "postgresql"
fi


# =======
# Hotkeys
# =======

starting "Hotkeys"

if [ -d "/Applications/Karabiner-Elements.app" ]; then
    if pgrep -qf "Karabiner-Elements"; then
        success "karabiner-elements installed and running"
    else
        warning "karabiner-elements installed but not running — open it from /Applications"
    fi
else
    warning "karabiner-elements not installed — download from https://karabiner-elements.pqrs.org"
fi

# Symbolic hotkey IDs and keys for built-in window tiling
TILE_LEFT_ID=240;   KEY_H_UNICODE=104; KEY_H_CODE=4
TILE_RIGHT_ID=241;  KEY_L_UNICODE=108; KEY_L_CODE=37
TILE_FILL_ID=237;   KEY_K_UNICODE=107; KEY_K_CODE=40
TILE_CENTER_ID=238; KEY_J_UNICODE=106; KEY_J_CODE=38
ARRANGE_LR_ID=248; ARRANGE_RL_ID=249
# Modifier flags: ctrl (0x40000) + cmd (0x100000) = 0x140000
CTRL_CMD_FLAGS=1310720
# Modifier flags: ctrl (0x40000) + shift (0x20000) + cmd (0x100000) = 0x160000
CTRL_SHIFT_CMD_FLAGS=1441792

# Write through CFPreferences (not directly to disk) so cfprefsd notifies subscribers
remap_tiling() {
    python3 <<EOF
import plistlib, subprocess, sys
result = subprocess.run(['defaults', 'export', 'com.apple.symbolichotkeys', '-'], capture_output=True)
prefs = plistlib.loads(result.stdout)
hotkeys = prefs.setdefault('AppleSymbolicHotKeys', {})
entry = lambda u, k: {'enabled': True, 'value': {'parameters': [u, k, $CTRL_CMD_FLAGS], 'type': 'standard'}}
hotkeys['$TILE_LEFT_ID']   = entry($KEY_H_UNICODE, $KEY_H_CODE)
hotkeys['$TILE_RIGHT_ID']  = entry($KEY_L_UNICODE, $KEY_L_CODE)
hotkeys['$TILE_FILL_ID']   = entry($KEY_K_UNICODE, $KEY_K_CODE)
hotkeys['$TILE_CENTER_ID'] = entry($KEY_J_UNICODE, $KEY_J_CODE)
entry2 = lambda u, k: {'enabled': True, 'value': {'parameters': [u, k, $CTRL_SHIFT_CMD_FLAGS], 'type': 'standard'}}
hotkeys['$ARRANGE_LR_ID'] = entry2($KEY_H_UNICODE, $KEY_H_CODE)
hotkeys['$ARRANGE_RL_ID'] = entry2($KEY_L_UNICODE, $KEY_L_CODE)
r = subprocess.run(['defaults', 'import', 'com.apple.symbolichotkeys', '-'], input=plistlib.dumps(prefs))
sys.exit(r.returncode)
EOF
    /System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings -u
}

verify_tiling() {
    python3 <<EOF
import plistlib, subprocess, sys
result = subprocess.run(['defaults', 'export', 'com.apple.symbolichotkeys', '-'], capture_output=True)
prefs = plistlib.loads(result.stdout)
hotkeys = prefs.get('AppleSymbolicHotKeys', {})
def check(id_, unicode_, code, flags=$CTRL_CMD_FLAGS):
    params = hotkeys.get(str(id_), {}).get('value', {}).get('parameters', [])
    return params == [unicode_, code, flags]
ok = (check($TILE_LEFT_ID,   $KEY_H_UNICODE, $KEY_H_CODE) and
     check($TILE_RIGHT_ID,  $KEY_L_UNICODE, $KEY_L_CODE) and
     check($TILE_FILL_ID,   $KEY_K_UNICODE, $KEY_K_CODE) and
     check($TILE_CENTER_ID, $KEY_J_UNICODE, $KEY_J_CODE) and
     check($ARRANGE_LR_ID, $KEY_H_UNICODE, $KEY_H_CODE, $CTRL_SHIFT_CMD_FLAGS) and
     check($ARRANGE_RL_ID, $KEY_L_UNICODE, $KEY_L_CODE, $CTRL_SHIFT_CMD_FLAGS))
sys.exit(0 if ok else 1)
EOF
}

if remap_tiling; then
    killall WindowManager 2>/dev/null || true
    if verify_tiling; then
        success "window tiling hotkeys applied and verified"
    else
        failure "window tiling hotkeys applied but verification failed"
    fi
else
    failure "window tiling hotkeys could not be written"
fi

mkdir -p "$HOME/.config/karabiner"
karabiner_src="$DOTFILES/karabiner/karabiner.json"
karabiner_dest="$HOME/.config/karabiner/karabiner.json"
if [ ! -f "$karabiner_dest" ]; then
    cp "$karabiner_src" "$karabiner_dest" && echo "${_INDENT}🔗 Copied: ${karabiner_dest/#$HOME/~}"
elif diff -q "$karabiner_src" "$karabiner_dest" &>/dev/null; then
    success "karabiner config up to date"
else
    diff_files "$karabiner_src" "$karabiner_dest" "dotfiles" "~/.config"
    if ask "Replace ${karabiner_dest/#$HOME/~} with dotfiles version?"; then
        cp "$karabiner_src" "$karabiner_dest" && success "karabiner config updated"
    else
        skipping "karabiner config"
    fi
fi

# =======================
# Machine-local overrides
# =======================
#
# These files are not versioned. Each machine sets them independently.
# Naming convention: *.work for all local override files.
#   ~/.gitconfig.work    — included by .gitconfig for ~/Projects/ repos
#   ~/.zshrc.work        — sourced by .zshrc if present
#   bash/aliases.work.sh — sourced by aliases.sh if present

starting "Machine-local overrides"

if [ -f "$HOME/.gitconfig.work" ]; then
    success "~/.gitconfig.work already exists"
else
    cat > "$HOME/.gitconfig.work" <<'EOF'
[user]
	name = your-work-name
	email = your-work-email@example.com
EOF
    warning "Created stub ~/.gitconfig.work — update with your work git identity"
fi

if [ -f "$HOME/.zshrc.work" ]; then
    success "~/.zshrc.work already exists"
else
    cat > "$HOME/.zshrc.work" <<'EOF'
# Machine-local shell settings (not version controlled).
EOF
    warning "Created stub ~/.zshrc.work — add machine-local shell settings here"
fi

if [ -f "$DOTFILES/bash/aliases.work.sh" ]; then
    success "bash/aliases.work.sh already exists"
else
    skipping "bash/aliases.work.sh (create it manually for machine-local aliases)"
fi

# =============
# Link dotfiles
# =============

starting "Linking dotfiles"

link_file "$DOTFILES/.zshrc"            "$HOME/.zshrc"
link_file "$DOTFILES/.gitconfig"        "$HOME/.gitconfig"
link_file "$DOTFILES/.gitignore_global" "$HOME/.gitignore_global"
link_file "$DOTFILES/.inputrc"          "$HOME/.inputrc"
link_file "$DOTFILES/.pyrc"             "$HOME/.pyrc"
link_file "$DOTFILES/.tmux.conf"        "$HOME/.tmux.conf"
link_file "$DOTFILES/.config/workmux/config.yaml" "$HOME/.config/workmux/config.yaml"
link_file "$DOTFILES/.codex/hooks.json"       "$HOME/.codex/hooks.json"
link_file "$DOTFILES/.codex/notify.py"        "$HOME/.codex/notify.py"
link_file "$DOTFILES/.codex/codex_restore"    "$HOME/.codex/codex_restore"
link_file "$DOTFILES/.codex/save_resurrect_session_map.py" "$HOME/.codex/save_resurrect_session_map.py"
link_file "$DOTFILES/.codex/tmux_has_vim_on_tty.sh" "$HOME/.codex/tmux_has_vim_on_tty.sh"
link_file "$DOTFILES/.codex/rules/default.rules" "$HOME/.codex/rules/default.rules"
link_file "$DOTFILES/.claude/CLAUDE.md"        "$HOME/.claude/CLAUDE.md"
link_file "$DOTFILES/.claude/hooks"            "$HOME/.claude/hooks"
link_file "$DOTFILES/.claude/keybindings.json" "$HOME/.claude/keybindings.json"
link_file "$DOTFILES/.claude/settings.json"    "$HOME/.claude/settings.json"

if python3 "$DOTFILES/.codex/configure_notifications.py" "$DOTFILES/.codex/config.toml"; then
    success "codex notification settings updated"
else
    warning "codex notification settings could not be updated"
fi

link_file_with_backup "$DOTFILES/.codex/config.toml" "$HOME/.codex/config.toml"

# ======
# iTerm2
# ======

starting "iTerm2"

if [ -d "/Applications/iTerm.app" ] || [ -d "/Applications/iTerm2.app" ]; then
    ITERM_DYNAMIC_PROFILES_SRC="$DOTFILES/iterm2/DynamicProfiles/dotfiles-profiles.plist"
    ITERM_DYNAMIC_PROFILES_DEST="$HOME/Library/Application Support/iTerm2/DynamicProfiles/dotfiles-profiles.plist"
    ITERM_DYNAMIC_PROFILES_LEGACY_DEST="$HOME/Library/Application Support/iTerm2/DynamicProfiles/dotfiles-profiles.json"
    ITERM_DEFAULT_PROFILE_GUID="$(python3 - "$ITERM_DYNAMIC_PROFILES_SRC" <<'PY'
import plistlib, sys

with open(sys.argv[1], 'rb') as f:
    profiles = plistlib.load(f).get('Profiles', [])

for profile in profiles:
    if profile.get('Name') == 'Dotfiles Default':
        print(profile.get('Guid', ''))
        break
PY
)"

    if [ -L "$ITERM_DYNAMIC_PROFILES_LEGACY_DEST" ]; then
        rm "$ITERM_DYNAMIC_PROFILES_LEGACY_DEST" && success "removed legacy iTerm2 JSON profile link"
    elif [ -e "$ITERM_DYNAMIC_PROFILES_LEGACY_DEST" ]; then
        warning "${ITERM_DYNAMIC_PROFILES_LEGACY_DEST/#$HOME/~} is an old JSON profile file"
        if ask "Remove the legacy iTerm2 JSON profile file?"; then
            rm "$ITERM_DYNAMIC_PROFILES_LEGACY_DEST" && success "removed legacy iTerm2 JSON profile file"
        else
            warning "legacy iTerm2 JSON profile file left in place"
        fi
    fi

    link_file "$ITERM_DYNAMIC_PROFILES_SRC" "$ITERM_DYNAMIC_PROFILES_DEST"

    if [ -n "$ITERM_DEFAULT_PROFILE_GUID" ] && defaults write com.googlecode.iterm2 "Default Bookmark Guid" -string "$ITERM_DEFAULT_PROFILE_GUID"; then
        success "iTerm2 default profile set to Dotfiles Default"
    else
        warning "could not set the iTerm2 default profile"
    fi

    if pgrep -x iTerm2 &>/dev/null; then
        warning "restart iTerm2 to pick up default-profile changes for new windows"
    fi
else
    skipping "iTerm2 dynamic profiles (iTerm2.app not installed)"
fi

# ================
# tmux plugins
# ================

starting "tmux plugins"

if [ -f "$HOME/.tmux/plugins/tpm/bin/install_plugins" ]; then
    tmux start-server \; set-environment -g TMUX_PLUGIN_MANAGER_PATH "$HOME/.tmux/plugins/"
    "$HOME/.tmux/plugins/tpm/bin/install_plugins" &>/dev/null \
        && success "tmux plugins installed" \
        || warning "tmux plugin install failed — run 'prefix + I' inside tmux to retry"
else
    skipping "tmux plugins (tpm not installed)"
fi

# ========
# Complete
# ========

_INDENT=""
echo ""
complete "setup complete!"

echo ""
echo "  Open a new terminal (or run 'source ~/.zshrc' in zsh) to apply changes."
echo ""
