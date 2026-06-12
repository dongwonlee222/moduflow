---
name: git-native-artifact-model
description: Use when ModuFlow needs to create, update, validate, or explain issue, spec, task, status, PR, release, or roadmap artifacts stored in Git.
---

# Git-Native Artifact Model

Git is the durable state store.

## Git Preflight

Before initializing or executing GitHub Spec Kit-style work, verify:

- target project root
- local Git repo exists
- current Git root is not an accidental parent workspace
- GitHub `origin` exists when GitHub sync is expected
- `gh auth status` passes when GitHub issues, PRs, or releases should be created

If Git is missing, ask whether to run `git init` or switch to an existing repo.

If GitHub remote or `gh` auth is missing, continue in `git-files` mode unless the user explicitly wants GitHub sync.

## Required Links

Every artifact must reference:

- `issue_id`
- source request or opportunity
- owner or decision maker when known
- current phase
- next command

## Canonical Relationship

```text
Opportunity -> Issue -> Spec -> Analysis/Metrics -> Design/Prototype
            -> Plan/Tasks -> Status -> PR -> Release -> Update
```

Roadmap references issues and releases. It does not replace them.

## Modes

- `git-files`: durable Markdown/JSON artifacts are tracked in local Git.
- `github-sync`: Git artifacts remain canonical, while GitHub issue/PR/release objects mirror them.
