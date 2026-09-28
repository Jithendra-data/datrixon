# Datrixon identity and repository migration

Datrixon is the analytics product. The synthetic distribution business is fictional and has no shared product identity.

## Current repository and website

The repository was renamed from `northstar-distribution-intelligence` to `datrixon`. Application links, README links, social metadata and the Git remote use the new name.

- Repository: https://github.com/Jithendra-data/datrixon
- Application: https://jithendra-data.github.io/datrixon/
- Architecture: https://jithendra-data.github.io/datrixon/#architecture

Use the new website address for LinkedIn and shared bookmarks. A repository redirect must not be treated as proof that the old GitHub Pages website redirects. Existing analytics hash routes remain unchanged.

## Retained compatibility identifiers

- `NORTHSTAR_RANDOM_SEED` and `NORTHSTAR_BROWSER_CHANNEL`: existing configuration interfaces retained for compatibility.
- `NorthStarAnalytics` in proposed T-SQL: database identifier in a separate deployment design, not the public product title.
- Workflow concurrency/artifact identifiers: retained to avoid splitting refresh groups and breaking historical artifact references.
- `NS-` product SKUs: synthetic source identifiers, not application branding.
- Historical commits: unchanged historical evidence. Current documentation links Datrixon release screenshots.
