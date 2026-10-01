# ERP / Dynamics 365 Finance & Operations orientation

**Conceptual architecture only — no live D365 integration or Microsoft-specific table/API implementation.** Datrixon demonstrates familiar ERP reporting grains and controls; it does not recreate an ERP or certify accounting balances.

| ERP domain | Datrixon evidence | Production discovery / replacement |
|---|---|---|
| Sales | Separate order headers/lines and posted invoices | Approved posting, cancellation, fulfillment and credit-note semantics |
| Accounts Receivable | Invoice/customer linkage only | Customer transactions, settlements, aging, credits and reconciliation to subledger |
| General Ledger | Not modeled | Posting vouchers, chart of accounts, close periods and GL/subledger reconciliation |
| Accounts Payable | Not modeled; PO commitments are not AP liabilities | Vendor invoice, matching, settlement and liability definitions |
| Procurement | PO line, receipt events, remaining quantities | Approved entities, status transitions and receipt/invoice matching |
| Inventory / WMS | Signed movement ledger by product/warehouse | Units, locations, inventory dimensions, financial/physical valuation and movement identity |
| Customers / CRM | Customer master, region, activity | Party/customer keys, effective-dated territory, consent and source ownership |
| Vendors | Vendor master, receipt quantities and lead times | Supplier identities, purchase policies and agreed performance grain |
| Products | Product master, category, current/transaction costs | Released-product keys, units, conversions, cost methods and dimensions |
| Warehouses | Four synthetic warehouses | Site/warehouse/location crosswalks and legal-entity scope |
| Legal entities | Main scenario implicitly one fictional US distributor; standalone adapter includes legal_entity | Explicit entity dimension and tenant isolation before combining entities |
| Financial dimensions | Not modeled | Governed dimensional combinations and accounting mappings |
| Currency | Synthetic USD only | Transaction/accounting/reporting currency and approved FX rules |
| Fiscal periods | Calendar year/month reporting, not a corporate fiscal calendar | Approved fiscal calendar, adjustment periods and close-state policy |

An enterprise extraction boundary would emit authenticated batch identity, legal entity, source key, schema version, currency, unit, effective timestamp and source control totals. Land immutable authorized extracts, validate their contracts, normalize crosswalks, reconcile before and after modeling, and expose only authorized semantic measures. The tested standalone mock change adapter demonstrates versions/tombstones and replay; it is not connected to a Microsoft tenant.

Existing analytics were not expanded with artificial GL balances or guessed financial dimensions. Those require real business definitions and source-owner approval. This keeps portfolio evidence technically honest and preserves V1 calculations.
