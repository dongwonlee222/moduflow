# Session: 086 Dashboard Design Review

Issue: `086-project-aware-production-library-dashboard`
Date: 2026-07-10
Owner / reviewer: Dongwon Lee
Phase: design review -> plan ready
Next: `product:plan 086-project-aware-production-library-dashboard`

## Decisions

- Preserve the existing generated ModuFlow Issue DB and Cytoscape issue/knowledge graphs instead of recreating them with sample markup.
- Read the project name from registered ModuFlow metadata; the current repository displays `ModuFlow`, not an illustrative external project.
- Keep Production Records and Playbooks as additive tabs.
- Use a dimmed modal for long Production Record detail when a selected project has registered records.
- Keep the current active issue focused in the issue graph.

## Correction

Issue 086 was mistakenly left in backlog while design work was active. Because the graph focuses `status=active` nodes, the current-work focus disappeared. The issue and derived state were corrected to active before implementation planning.
