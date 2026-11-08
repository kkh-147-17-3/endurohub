# Historical comparison fixtures

This directory preserves the actual pre-change UI for the user's requested before/after comparison. Its dots, repeated metadata and original typography are historical evidence, so do not apply the current visual cleanup rules to these snapshots.

Make production design changes in `web/src/lib` and `web/src/routes`. Refresh this baseline only from an explicitly chosen Git commit, record that commit and any import-path rewrites in `provenance.json`, and keep the source unchanged apart from those rewrites. Inject the stored baseline global CSS only inside the isolated BEFORE preview.
