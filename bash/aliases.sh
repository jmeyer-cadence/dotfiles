# ========
# Dotfiles
# ========

alias src="source $HOME/.zshrc"
alias zc="$EDITOR ~/.zshrc"

alias df="cd $HOME/dotfiles"

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
alias gpomr="git pull origin master --rebase"
alias gd="git diff"
alias gdl="git show"
alias gst="git status"
alias gstl="git show --name-status HEAD"
alias ghi="git log --graph --abbrev-commit --branches --remotes --tags --graph --oneline --decorate --format=format:'%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%s%C(reset) %C(dim white)- %an%C(reset)%C(bold yellow)%d%C(reset)'"
alias gprune="git remote prune origin && git branch --merged master | grep -v '^[ *]*master$' | xargs git branch -d"
alias gtempignore="git update-index --assume-unchanged"
alias gtempunignore="git update-index --no-assume-unchanged"

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
