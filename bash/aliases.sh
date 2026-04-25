# ========
# Dotfiles
# ========

alias src="source $HOME/.zshrc"
alias zc="$EDITOR ~/.zshrc"

dotfiles_repo_root() {
    printf '%s\n' "$HOME/dotfiles"
}

dotfiles_worktree_root() {
    printf '%s\n' "$HOME/dotfiles__worktrees"
}

dotfiles_worktree_slug() {
    local name="${1:-active}"
    printf '%s\n' "${name//\//-}"
}

dotfiles_worktree_branch() {
    local name="${1:-active}"
    printf 'dotfiles/%s\n' "$name"
}

dotfiles_worktree_path() {
    local name="${1:-active}"
    printf '%s/%s\n' "$(dotfiles_worktree_root)" "$(dotfiles_worktree_slug "$name")"
}

dotfiles_worktree_create() {
    local name="${1:-active}"
    local repo path branch default_branch base_ref

    repo="$(dotfiles_repo_root)"
    path="$(dotfiles_worktree_path "$name")"
    branch="$(dotfiles_worktree_branch "$name")"

    if [ -d "$path" ]; then
        printf '%s\n' "$path"
        return 0
    fi

    mkdir -p "$(dotfiles_worktree_root)" || return 1

    default_branch="$(git_default_branch_at "$repo")" || return 1
    if git -C "$repo" show-ref --verify --quiet "refs/remotes/origin/$default_branch"; then
        base_ref="origin/$default_branch"
    elif git -C "$repo" show-ref --verify --quiet "refs/heads/$default_branch"; then
        base_ref="$default_branch"
    else
        printf 'dotfiles: unable to find base ref for %s\n' "$default_branch" >&2
        return 1
    fi

    if git -C "$repo" show-ref --verify --quiet "refs/heads/$branch"; then
        git -C "$repo" worktree add "$path" "$branch" || return 1
    else
        git -C "$repo" worktree add -b "$branch" "$path" "$base_ref" || return 1
    fi

    printf '%s\n' "$path"
}

df() {
    local name="${1:-active}"
    local path

    path="$(dotfiles_worktree_create "$name")" || return 1
    cd "$path" || return 1
}
alias dfm="cd $HOME/dotfiles"

dfsync() {
    local name="${1:-}"
    local repo current_root current_origin repo_origin branch path default_branch

    repo="$(dotfiles_repo_root)"
    default_branch="$(git_default_branch_at "$repo")" || return 1

    if [ -n "$name" ]; then
        branch="$(dotfiles_worktree_branch "$name")"
        path="$(dotfiles_worktree_path "$name")"
    else
        current_root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
            printf 'dfsync: pass a worktree name or run this from a dotfiles worktree\n' >&2
            return 1
        }
        current_origin="$(git config --get remote.origin.url 2>/dev/null)"
        repo_origin="$(git -C "$repo" config --get remote.origin.url 2>/dev/null)"
        if [ -z "$current_origin" ] || [ "$current_origin" != "$repo_origin" ]; then
            printf 'dfsync: run this from a dotfiles worktree or pass a worktree name\n' >&2
            return 1
        fi
        branch="$(git branch --show-current 2>/dev/null)" || return 1
        path="$current_root"
    fi

    if [ "$path" = "$repo" ]; then
        printf 'dfsync: use a dotfiles worktree, not the landing checkout\n' >&2
        return 1
    fi

    git -C "$repo" merge --ff-only "$branch" || return 1

    if [ -d "$path" ]; then
        git -C "$path" rebase "$default_branch" || return 1
    fi
}

dfwork() {
    local name="${1:-active}"
    local path session

    path="$(dotfiles_worktree_create "$name")" || return 1
    if [ "$name" = "active" ]; then
        session="dfwork"
    else
        session="dfwork-$(dotfiles_worktree_slug "$name")"
    fi

    cd "$path" || return 1
    tmux new-session -A -s "$session" -c "$path"
}

# =======
# General
# =======

alias ls="/opt/homebrew/bin/gls --color -h --group-directories-first"
alias sl=ls
alias la="/opt/homebrew/bin/gls --color -hla --group-directories-first"
alias fif=find_in_file
alias fifi=find_in_file_with_ignore

find_in_file() {
    rg --no-ignore -i $1
}
find_in_file_with_ignore() {
    rg --no-ignore -i $1
}

# ===
# Git
# ===

alias ga="git add"
alias grm="git rm"
alias gbr="git branch"
alias gco="git checkout"
alias gcom="git commit -m"
alias gam="git commit --amend"
alias gamne="git commit --amend --no-edit"
alias gpfwl="git push --force-with-lease"
alias gd="git diff"
alias gdl="git show"
alias gst="git status"
alias gstl="git show --name-status HEAD"
alias ghi="git log --graph --abbrev-commit --branches --remotes --tags --graph --oneline --decorate --format=format:'%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%s%C(reset) %C(dim white)- %an%C(reset)%C(bold yellow)%d%C(reset)'"
alias gtempignore="git update-index --assume-unchanged"
alias gtempunignore="git update-index --no-assume-unchanged"

git_default_branch_at() {
    local repo="$1"
    local origin_head

    origin_head="$(git -C "$repo" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)"
    if [ -n "$origin_head" ]; then
        printf '%s\n' "${origin_head#origin/}"
    elif git -C "$repo" show-ref --verify --quiet refs/remotes/origin/main; then
        printf 'main\n'
    elif git -C "$repo" show-ref --verify --quiet refs/remotes/origin/master; then
        printf 'master\n'
    else
        printf 'main\n'
    fi
}

git_default_branch() {
    git_default_branch_at .
}

git_pull_origin_default_rebase() {
    git pull origin "$(git_default_branch)" --rebase
}
alias gpomr=git_pull_origin_default_rebase

# Default new workmux worktrees to the latest upstream default branch.
workmux_add_uses_custom_base() {
    local arg

    for arg in "$@"; do
        case "$arg" in
            --base|--base=*|--pr|--pr=*)
                return 0
                ;;
        esac
    done

    return 1
}

workmux_latest_default_base() {
    local default_branch

    default_branch="$(git_default_branch)" || return 1

    if git show-ref --verify --quiet "refs/remotes/origin/$default_branch"; then
        git fetch origin "$default_branch" >/dev/null 2>&1 || \
            printf 'workmux: warning: unable to refresh origin/%s; using cached ref\n' "$default_branch" >&2
        printf 'origin/%s\n' "$default_branch"
        return 0
    fi

    if git show-ref --verify --quiet "refs/heads/$default_branch"; then
        printf '%s\n' "$default_branch"
        return 0
    fi

    return 1
}

workmux() {
    if [ "$1" = "add" ]; then
        shift

        if ! workmux_add_uses_custom_base "$@"; then
            local base_ref

            base_ref="$(workmux_latest_default_base)" || {
                command workmux add "$@"
                return $?
            }

            command workmux add --base "$base_ref" "$@"
            return $?
        fi

        command workmux add "$@"
        return $?
    fi

    command workmux "$@"
}

git_prune_merged_default() {
    local default_branch

    default_branch="$(git_default_branch)"
    git remote prune origin || return 1
    git branch --merged "origin/$default_branch" |
        grep -Ev '(^\*|^[[:space:]]*(main|master|dev)$)' |
        while read -r branch; do
            git branch -d "${branch##* }"
        done
}
alias gprune=git_prune_merged_default

# Worktrees — siblings to the current worktree's parent (bare repo layout)
git_worktree_add() {
    local name="$1"; shift
    git worktree add "$(dirname "$(git rev-parse --show-toplevel)")/$name" "$@"
}
git_worktree_remove() {
    local name="$1"
    git worktree remove "$(dirname "$(git rev-parse --show-toplevel)")/$name"
}
alias gwt=git_worktree_add
alias gwtrm=git_worktree_remove
alias gwtls="git worktree list"

# should delete branches on local that have been merged to $1 (recommend: upstream or origin)
# usage example: "gclean upstream main"
git_clean_local_merged() {
    git branch --merged $1/$2 | grep -Ev "(^\*|main|master|dev)" | xargs -n 1 git branch -d
}
alias gclean=git_clean_local_merged

# ========
# Intellij
# ========
alias idea="/Applications/IntelliJ\ IDEA.app/Contents/MacOS/idea"

# =======
# Aliases
# =======

alias ae="vim $HOME/dotfiles/bash/aliases.sh"
alias aew="vim $HOME/dotfiles/bash/aliases.work.sh"

refresh_aliases() {
    . $HOME/dotfiles/bash/aliases.sh

    # Optionally source work aliases if they exist
    if [ -f $HOME/dotfiles/bash/aliases.work.sh ]; then
      . $HOME/dotfiles/bash/aliases.work.sh
    fi
}
alias ar=refresh_aliases

# Optionally source work aliases if they exist
if [ -f $HOME/dotfiles/bash/aliases.work.sh ]; then
  . $HOME/dotfiles/bash/aliases.work.sh
fi
