---
name: index
description: Use when the ModuFlow plugin is at-mentioned directly, or when the user says product:start, product:status, product:inbox, product:issue, product:spec, product:roadmap, product:plan, product:execute, product:review, product:pr, product:release, product:update, ModuFlow, 모두플로우, 모두의 플로우, PM workflow, roadmap workflow, Git issue workflow, or asks to start/manage product execution with Git-native issues and specs.
---

# ModuFlow Index

ModuFlow routes product work through Git-native artifacts.

## Codex Invocation

Codex reserves leading `/` for native slash commands. Treat these as equivalent:

- `product:start`
- `/product:start`
- `ModuFlow 시작`
- `모두플로우 시작`

## Command Map

- `product:start`: initialize project artifacts
- `product:migrate`: plan or apply a safe migration for an existing project
- `product:profile`: create or inspect project profile metadata
- `product:inbox`: capture raw requests
- `product:opportunity`: shape opportunity/problem
- `product:issue`: create or update Git issue artifact
- `product:spec`: create spec/PRD
- `product:analyze`: run metrics/data analysis
- `product:design`: create UX/design brief
- `product:prototype`: create or review prototype
- `product:roadmap`: update roadmap view
- `product:plan`: create execution plan/tasks
- `product:execute`: run implementation workflow
- `product:status`: show state and next action
- `product:review`: review PM/UX/data/QA/release gates
- `product:pr`: prepare PR
- `product:release`: prepare release
- `product:update`: create stakeholder update
- `product:sync`: inspect or update upstream sources
- `product:doctor`: validate setup

## Behavior

1. Identify the project root before writing files.
2. Run Git preflight before `product:start`, `product:migrate`, `product:profile`, `product:issue`, `product:spec`, `product:plan`, `product:execute`, `product:pr`, or `product:release`.
3. If no project root is clear, ask for the target project.
4. Keep Git as the source of truth.
5. Always end with the next recommended ModuFlow command.
