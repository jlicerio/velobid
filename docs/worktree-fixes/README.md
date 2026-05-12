# Worktree Fix Log

Use this directory to track active and completed fixes tied to worktrees, deployments, and follow-up updates.

## Why this exists

- Keep one durable place for what we changed, where it was changed, and what still needs follow-up.
- Make handoffs easier between sessions and branches.
- Keep deployment-impact notes close to the codebase.

## File naming

Create one file per fix using:

`YYYY-MM-DD-<short-fix-name>.md`

Example:

`2026-05-11-chat-blank-stream.md`

## Required fields in each fix file

- Worktree path
- Branch name
- GitHub issue/PR links
- Problem summary
- Root cause
- Fix implemented
- Deployment impact
- Verification steps + results
- Suggested next fixes

## Process

1. Create a new fix file from `TEMPLATE.md` when starting work.
2. Update the same file during implementation and testing.
3. Mark status as `done` only after verification.
4. Keep suggested follow-ups at the bottom so the next worktree starts fast.
