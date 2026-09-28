# Executed Datrixon model

Source CSV values are normalized by Python. The executed warehouse is SQLite; monetary amounts are REAL with explicit tolerance. T-SQL decimal/surrogate-key designs are separate and not loaded.

| Table | Key / grain | Retained evidence |
|---|---|---|
| FactSales | InvoiceID + LineNumber | Invoice date, customer, product, warehouse, rep, order, posted status, quantity, revenue, COGS, discount, GP |
| FactInventory | InventoryTransactionID | Date, product, warehouse, signed quantity, movement type, source reference, movement cost |
| FactPurchasing | PONumber + LineNumber | Created date, expected date, vendor, product, warehouse, ordered/received/remaining quantities, unit cost |
| FactReturns | ReturnID | Date, customer, product, invoice-line reference, quantity, amount, reason |
| PurchaseReceiptEvent | ReceiptID, child of PO line | PO number + line number, receipt date, quantity; multiple events allowed |

Six natural-key dimensions: Date, Customer, Product, Vendor, SalesRep, Warehouse. DateKey is ISO date text, covering 2020–2035. Masters represent current attributes, not SCD2 history. Source keys, foreign keys, arithmetic and lifecycle constraints block publication.

Public compatibility names: LifetimeRevenue means historical invoiced revenue in the available scenario, not lifetime value. AvailableQty means signed ledger on-hand, not available-to-promise. dead_inventory_value is a legacy contract field for positive stock with no shipments in the trailing movement window, not proven obsolete stock. These internal field names are retained to avoid unnecessary contract breakage; UI labels state the measured definition.

Current source and target column details are executable in sql/sqlite/warehouse.sql and etl/warehouse.py. Product UnitCost is the current standard cost; invoice UnitCost captures the transaction's generated cost and can differ.
