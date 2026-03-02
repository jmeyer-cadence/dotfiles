# Global Claude Code Instructions

<!--
  This file applies to all Claude Code sessions across every project.
  Use it for personal preferences, workflow conventions, and cross-project standards.
  Project-level CLAUDE.md files (checked into each repo) take precedence over this file.
-->

# Dotfiles

If you detect improvements or changes that should be made to dotfiles, go ahead and make them. Always ensure changes are committed to git so history is tracked and a human can review or revert if needed. Never amend or rewrite existing git history — always create new commits.

If a change introduces a new tool or CLI dependency, add a corresponding install block to `install.sh` following the existing pattern (check if installed, prompt to install via brew, skip if declined).

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
