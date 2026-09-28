# Datrixon identity and URL migration

Datrixon is the analytics product. The synthetic distribution business is fictional and has no shared product identity.

## Classification of retained identifiers

- `northstar-distribution-intelligence` in public URLs and Git remote: retained deployment/repository slug, not product branding. GitHub Pages project URLs cannot be assumed to redirect after a repository rename.
- `NORTHSTAR_RANDOM_SEED` and `NORTHSTAR_BROWSER_CHANNEL`: existing configuration interfaces, retained for compatibility.
- `NorthStarAnalytics` in proposed T-SQL: existing database identifier; not a deployed product title.
- Workflow concurrency/artifact identifiers: retained to avoid splitting concurrent refresh groups and breaking historical artifact references.
- `NS-` product SKUs: synthetic source identifiers, not application branding.
- Historical commits: historical evidence. Old screenshots are retired from the current tree; documentation links reviewed Datrixon captures.

## Optional repository migration

Keep the existing URL working for this release. In GitHub repository Settings > General, confirm `datrixon` is available, then rename the repository. Update origin, README/docs links, web JavaScript GitHub links, Open Graph/canonical URLs and preview asset URLs. Re-run Pages on the new repository and check every route and asset.

Expected new URLs (not currently claimed live):
- https://github.com/Jithendra-data/datrixon
- https://jithendra-data.github.io/datrixon/

Verify the old Pages URL explicitly. If it stops working, publish a redirect page from a separate repository retaining the old slug; do not assume GitHub repository redirects cover Pages. Confirm both URLs before advertising the migration.
