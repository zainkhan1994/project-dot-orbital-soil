# Issue tracker: GitHub

Issues for this repo live as GitHub issues at https://github.com/zainkhan1994/project-dot-orbital-soil/issues. Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`
- **Read an issue**: `gh issue view <number> --json number,title,body,labels,comments`
- **List issues**: `gh issue list --state open --json number,title,labels`
- **Comment**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

`gh` infers the repo from `git remote -v` when run inside a clone.

**PRs as a request surface: no.**
