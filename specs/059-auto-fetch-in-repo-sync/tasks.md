# Tasks: Auto Fetch In Repo Sync

Issue: `059-auto-fetch-in-repo-sync`

- [x] Create issue/spec/plan artifacts
- [ ] Write RED tests for fetch success/failure/timeout
- [ ] Add timeout handling to `run_command`
- [ ] Call `git fetch --quiet` first in `inspect_repo_sync`, add `fetched`/`fetch_warning` fields
- [ ] Prepend stale-cache recommendation when fetch fails
- [ ] Update existing `FakeRunner` fixtures with a fetch response
- [ ] Update `product:sync` docs (fetch is automatic)
- [ ] Update `product:status` docs (fetch is automatic)
- [ ] Run focused test suite
- [ ] Run release check
- [ ] Mark issue workflow tasks complete

## Next Command

`product:execute 059-auto-fetch-in-repo-sync`
