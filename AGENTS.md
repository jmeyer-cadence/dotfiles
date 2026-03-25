# Dotfiles Instructions

The canonical dotfiles repo lives at `~/dotfiles` on `master`.

Shell config symlinks (for example `~/.zshrc`) should point to files in the
main repo, not to a worktree.

When changing dotfiles:
- Prefer reusable changes in the repo over one-off edits in `$HOME`.
- Wire user-facing dotfile files into place through `./install.sh`.
- For files that should live in `$HOME`, prefer symlinks created by `./install.sh`.
- Do not copy files directly into `$HOME` as a substitute for the repo + install flow.
- Do not assume a worktree change is live in `~/dotfiles` until it has been
  merged into `master`.
- If a change introduces a new tool or CLI dependency, add a matching install
  block to `install.sh`.

Worktree flow:
1. Make the change on the worktree branch first.
2. When the user wants it merged, fast-forward `~/dotfiles` (`master`) to the
   worktree branch.
3. Rebase the worktree branch onto `master` after that fast-forward.
4. Never make the same change independently in both `master` and a worktree.

# Code Comments

Do not describe implementation details in comments outside the function where
those details live. Call-site comments should explain intent or why, not the
mechanics of the called function.
