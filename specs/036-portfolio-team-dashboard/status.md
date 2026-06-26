# Status: Portfolio Team Dashboard

## Issue

`036-portfolio-team-dashboard`

## Current Phase

Done.

## Done

- Extended `scripts/project_portfolio.py` to read `workflow/team-state.json`.
- Added active/review/done team summaries to project status collection.
- Added Active Work and Review columns to portfolio dashboard output.
- Added team workflow summaries to weekly status output.
- Updated `product:portfolio` docs.
- Bumped ModuFlow to 0.2.15.

## Verification

- `python3 -m unittest tests.test_project_portfolio -v` passed.
- `python3 -m unittest discover -s tests -v` passed.
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Next Command

`/product:status`
