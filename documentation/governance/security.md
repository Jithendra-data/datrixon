# Security and demo policy boundary

**SIMULATED / DEMONSTRATED:** Executive, Finance, Sales, Operations, Data Analyst, Data Engineer and Administrator roles. `governance/policies/access.json` defines domain coverage; each metric also has permitted roles. Both constraints must allow the request. Unknown roles, unknown operations, uncertified metrics, failed trust and Restricted classification deny access. Administrator has no Restricted AI bypass.

The raw synthetic Customer address column is classified Restricted and is not present in assistant answers. CreditLimit is classified Confidential and is not exported through the semantic interface. Field names/classifications can appear in contract documentation without revealing field values. All remaining public records are synthetic; classification labels demonstrate governance behavior, not confidentiality guarantees.

GitHub Pages serves public bytes. Visitors can download the JSON regardless of the role selector. **Demo role simulation — not production authentication.** Never place real confidential data in `web/` or public Actions evidence bundles.

## Implemented protections

- Fixed query IDs and bound SQL parameters; read-only SQLite connection and statement authorizer.
- No user-controlled filesystem path or SQL interface in the assistant.
- Unsupported natural-language requests refused instead of approximated.
- Escaped HTML for user questions, metadata, result values and provenance.
- Restricted requests denied and no result rows returned on policy failure.
- Session audit omits question text and record values; pipeline audit omits source values and secrets.
- Source-tree credential-pattern scanner in CI; no API keys or paid service required.

## Production replacement

Move data behind an authenticated API. Verify OIDC/OAuth tokens against the corporate identity provider (for example Entra ID), derive entitlements server-side, enforce tenant/legal-entity scope and warehouse RLS, and test cross-tenant denial. Use managed identities/secrets, encrypted restricted storage, retention, tamper-evident audit and approved incident response. Add CSP, dependency integrity policy, supply-chain scanning and a security review suited to the actual deployment. Current pattern scanning and browser tests are not a security certification.
