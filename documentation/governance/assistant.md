# Governed analytical assistant and provenance

The implemented provider is `LocalAnalyticalProvider` in `web/js/governed-ai.js`. It recognizes a bounded grammar, including annual revenue, gross margin/profit, inventory measures, customer inactivity, overdue PO investigations, monthly revenue, controls, lineage and inventory readiness. Unsupported periods, filters or questions return a controlled refusal.

The assistant does not use an LLM, embeddings, external API or generated SQL. Questions are untrusted strings, never code. Responses are assembled from approved semantic values, SQL-precomputed annual values, existing capped investigation extracts and governance metadata. The margin-change answer explains arithmetic and explicitly avoids causal inference.

Each result carries answer ID, original bounded question, timestamp, cutoff, metric IDs and versions, executed logic/SQL, source dependencies, trust/control decisions, reconciliation evidence, lineage reference, role policy decision and dataset version. Citations navigate to definitions and lineage. Denied answers contain reasons and the last approved version; they contain no result rows.

Question text is visible only in the in-memory answer provenance panel. Session audit records omit question and record values. Reload clears session evidence. No multi-user history or immutable access log is implemented.

## Future provider integration

A server-side provider may implement the same answer interface or propose a strictly validated operation. It must never bypass the semantic allowlist, certification, freshness, policy or reconciliation checks. Put credentials in the deployment secret store, not browser code. Enforce roles from a verified identity at the server. The current client-side gate is an educational demonstration and cannot protect data already downloaded as public JSON.
