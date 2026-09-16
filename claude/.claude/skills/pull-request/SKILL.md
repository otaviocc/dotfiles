---
name: pull-request
description: Draft a concise pull request description from the branch's changes and open it as a draft PR with gh after confirmation. Use when asked to open, create, or write a pull request or PR, or to update an existing PR's description.
---

# Pull Request

Reads the branch's commits and diff, drafts a **short, readable** PR description, shows it to the user, and only then opens the PR with `gh` — always as a **draft**, always assigned to the user.

The description is written for someone who is about to read the diff, not instead of it. Explain intent and trade-offs; let the code carry the mechanics.

## Prerequisites

- `gh` installed and authenticated (`gh auth status`).
- The current branch is not the base branch, and has at least one commit the base doesn't.

## Workflow

1. **Settle the base branch first — never assume the default branch.** In order:
   - If the user named a base ("against develop", "onto release/25.3", "into the hotfix branch"), use it verbatim.
   - Otherwise infer it: check what this branch actually forked from with `git merge-base`, the conventions visible in `git branch -r` (`develop`, `release/*`, `hotfix/*`, `main`/`master`), and what recent PRs target (`gh pr list --state all --limit 20 --json baseRefName`).
   - If more than one base is plausible, **ask the user which one** before drafting. Getting this wrong makes the whole diff wrong.
2. Read the range: `git log <base>..HEAD` and `git diff <base>...HEAD --stat`. Three dots — the merge-base diff, so commits already on the base don't leak into the description.
3. Read the actual diff for anything whose intent isn't obvious from the commit messages.
4. Check for an existing PR: `gh pr view --json number,title,body,baseRefName`. If one exists this becomes an edit of its body, not a new PR, and its base wins over step 1.
5. Draft the title and body (rules below).
6. **Show the draft and the base branch it targets, then stop.** Don't push, don't create.
7. On approval: push if the branch has no upstream (`git push -u origin HEAD`), then

   ```bash
   gh pr create --draft --assignee @me --base <base> \
       --title '<title>' --body-file <file>
   ```

   or `gh pr edit --body-file <file>` for an existing PR. Write the body to a file first (scratchpad) — never a shell-escaped `--body` string.
   - **Always `--draft`.** Marking it ready for review is the user's move.
   - **Always `--base`**, explicitly, even when it happens to be the default branch.
   - **Always `--assignee @me`.** If the repo rejects it (no push access, not assignable), retry without it and mention the assignment didn't stick — never let it block the PR.
8. Report the PR URL. One line.

## Writing the description

- **Title**: imperative mood, capitalized, ≤ ~60 chars, no trailing period.
- **Body: short prose. No headings, no bullet walls.** One paragraph on what the change does, then at most one or two more for what a reviewer couldn't infer — why this approach, what was deliberately left out, what still doesn't work.
- Bullets only when the change genuinely is a list of independent items (several unrelated areas touched). Never as a restatement of the file list.
- Aim for under ~150 words. **A one-line PR is a fine PR.**
- Mention testing **only if something was actually run in the session**, and say what was run. Never invent verification.
- If the branch name or commits carry an issue/ticket reference (`ABC-123`, `#456`), include it — a bare reference line is enough.
- Never add "Generated with Claude Code", `Co-Authored-By: Claude`, or any other AI attribution footer.

## What to avoid

No type, function or symbol names — that is what the diff is for:

> **Avoid:** Adds `FooViewModel.handleTap(_:)`, which calls `BarService.fetch()` and maps the result through `BazMapper`.
>
> **Prefer:** Tapping a row now loads the detail screen.

Also: no `Summary`/`Changes`/`Testing` section scaffolding, no file-by-file walkthrough, no restating the diff stat, no emoji.

## Notes

- Never force-push, never amend or rewrite commits, never mark a PR ready for review, never create a PR without explicit approval.
- If the target repo has a `.github/pull_request_template.md`, follow its structure — and apply these rules to the prose inside it.
