# Global Claude Code Instructions

<!--
  This file applies to all Claude Code sessions across every project.
  Use it for personal preferences, workflow conventions, and cross-project standards.
  Project-level CLAUDE.md files (checked into each repo) take precedence over this file.
-->

# Dotfiles

If you detect improvements or changes that should be made to dotfiles, go ahead and make them. Always ensure changes are committed to git so history is tracked and a human can review or revert if needed. Never amend or rewrite existing git history — always create new commits.

If a change introduces a new tool or CLI dependency, add a corresponding install block to `install.sh` following the existing pattern (check if installed, prompt to install via brew, skip if declined).
