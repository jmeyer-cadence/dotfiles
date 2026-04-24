# Global Claude Code Instructions

<!--
  This file applies to all Claude Code sessions across every project.
  Use it for personal preferences, workflow conventions, and cross-project standards.
  Project-level CLAUDE.md files (checked into each repo) take precedence over this file.
-->

# Dotfiles

If you detect improvements or changes that should be made to dotfiles, go ahead and make them. Always commit changes immediately after making them — never leave modified or untracked files unstaged. Never amend or rewrite existing git history — always create new commits.

The dotfiles repo lives at `~/dotfiles` (master branch). Shell config symlinks (e.g. `~/.zshrc`) point to files in the main repo, not to any worktree. When working in a worktree, always apply dotfile fixes to the main repo (`~/dotfiles`) as well so they take effect immediately.

Worktree workflow — always follow this order:
1. Commit all changes to the worktree branch first
2. Fast-forward master to match: `cd ~/dotfiles && git merge --ff-only <worktree-branch>`
3. Rebase the worktree branch onto master: `cd <worktree> && git rebase master`

Never commit the same change independently to both master and a worktree branch.

For workmux-managed worktrees, keep the default post-create sync behavior in `~/.config/workmux/config.yaml` so every agent rebases onto the repo's upstream default branch (`main`, `master`, or whatever `origin/HEAD` points to). In project `.workmux.yaml` files, include `'<global>'` in `post_create` when you want that global hook to apply.

Never enable auto-merge on a pull request unless the user has given express consent for that specific action. If auto-merge might be useful, ask first and wait for a clear yes.

If a change introduces a new tool or CLI dependency, add a corresponding install block to `install.sh` following the existing pattern (check if installed, prompt to install via brew, skip if declined).

# GitHub

When the GitHub connector is available, prefer GitHub connector or MCP tools for pull request, issue, review, comment, and repository reads and writes.

Use `gh` only when the connector does not cover the task well, specifically for:
- current-branch pull request discovery from local git context
- GitHub Actions logs and check diagnostics
- review-thread GraphQL fields not exposed by the connector
- local branch, commit, push, and other inherently local git operations

# Code Comments

Do not describe implementation details in comments outside the function where those details live. Call-site comments should describe *intent* or *why* — not the mechanics of what the called function does internally. Those mechanics belong in the function itself (or can be omitted entirely if the code is self-explanatory).

**Bad** — the comment leaks implementation details that belong inside `isNpLoadShedPatientEligible`:
```go
// If the NP load shedding lever is enabled, apply additional eligibility restrictions.
// When active, only HTN (<85 yrs) and CHF HFpEF (≤85 yrs) patients with appointments
// in the configured date range are eligible.
if s.isNpLoadShedEnabled() {
    if !s.isNpLoadShedPatientEligible(record) {
        return false, string(SkipReasonNpLoadShedIneligiblePatient)
    }
    ...
}
```

**Good** — the comment states intent only, details stay inside the called functions:
```go
// Apply additional eligibility restrictions when NP load shedding is active.
if s.isNpLoadShedEnabled() {
    if !s.isNpLoadShedPatientEligible(record) {
        return false, string(SkipReasonNpLoadShedIneligiblePatient)
    }
    ...
}
```

Or omit the comment entirely when the code reads clearly on its own. The risk of call-site implementation comments is that they silently go stale when the underlying function changes, misleading future readers.
