-- Executed reference warehouse. SQLite natural keys; T-SQL remains a separate design.
PRAGMA foreign_keys = ON;
CREATE TABLE DimDate(DateKey TEXT PRIMARY KEY, YearMonth TEXT NOT NULL);
CREATE TABLE DimCustomer(CustomerID TEXT PRIMARY KEY, CustomerName TEXT, Region TEXT);
CREATE TABLE DimProduct(ProductID TEXT PRIMARY KEY, ProductName TEXT, CategoryName TEXT, UnitCost REAL NOT NULL);
CREATE TABLE DimWarehouse(WarehouseID TEXT PRIMARY KEY, WarehouseName TEXT);
CREATE TABLE DimVendor(VendorID TEXT PRIMARY KEY, VendorName TEXT);
CREATE TABLE DimSalesRep(SalesRepID TEXT PRIMARY KEY, SalesRepName TEXT);
-- V2 reference table preserves booking/service grain without changing invoice facts.
CREATE TABLE OrderService(SalesOrderID TEXT PRIMARY KEY, OrderDate TEXT NOT NULL REFERENCES DimDate,
 ActualShipDate TEXT REFERENCES DimDate, RequestedShipDate TEXT NOT NULL, OrderStatus TEXT NOT NULL);
CREATE TABLE FactSales(InvoiceID TEXT, LineNumber INTEGER, DateKey TEXT NOT NULL REFERENCES DimDate,
 CustomerID TEXT NOT NULL REFERENCES DimCustomer, ProductID TEXT NOT NULL REFERENCES DimProduct,
 WarehouseID TEXT NOT NULL REFERENCES DimWarehouse, SalesRepID TEXT NOT NULL REFERENCES DimSalesRep,
 SalesOrderID TEXT NOT NULL, InvoiceStatus TEXT NOT NULL CHECK(InvoiceStatus='Posted'),
 Quantity REAL NOT NULL, Revenue REAL NOT NULL, COGS REAL NOT NULL, DiscountAmount REAL NOT NULL, GrossProfit REAL NOT NULL,
 PRIMARY KEY(InvoiceID,LineNumber));
CREATE TABLE FactInventory(InventoryTransactionID TEXT PRIMARY KEY, ProductID TEXT NOT NULL REFERENCES DimProduct,
 WarehouseID TEXT NOT NULL REFERENCES DimWarehouse, DateKey TEXT NOT NULL REFERENCES DimDate, Quantity REAL NOT NULL,
 TransactionType TEXT NOT NULL, ReferenceNumber TEXT NOT NULL, UnitCost REAL NOT NULL);
CREATE TABLE FactPurchasing(PONumber TEXT, LineNumber INTEGER, ProductID TEXT NOT NULL REFERENCES DimProduct,
 VendorID TEXT NOT NULL REFERENCES DimVendor, WarehouseID TEXT NOT NULL REFERENCES DimWarehouse,
 DateKey TEXT NOT NULL REFERENCES DimDate, ExpectedDeliveryDate TEXT NOT NULL,
 OrderedQuantity REAL NOT NULL, ReceivedQuantity REAL NOT NULL, RemainingQuantity REAL NOT NULL, UnitCost REAL NOT NULL,
 PRIMARY KEY(PONumber,LineNumber));
CREATE TABLE FactReturns(ReturnID TEXT PRIMARY KEY, CustomerID TEXT NOT NULL REFERENCES DimCustomer,
 ProductID TEXT NOT NULL REFERENCES DimProduct, DateKey TEXT NOT NULL REFERENCES DimDate,
 InvoiceID TEXT NOT NULL, InvoiceLineNumber INTEGER NOT NULL, ReturnReason TEXT NOT NULL,
 ReturnQuantity REAL NOT NULL, ReturnAmount REAL NOT NULL,
 FOREIGN KEY(InvoiceID,InvoiceLineNumber) REFERENCES FactSales(InvoiceID,LineNumber));
CREATE TABLE PurchaseReceiptEvent(ReceiptID TEXT PRIMARY KEY, PONumber TEXT NOT NULL, LineNumber INTEGER NOT NULL,
 DateKey TEXT NOT NULL REFERENCES DimDate, QuantityReceived REAL NOT NULL,
 FOREIGN KEY(PONumber,LineNumber) REFERENCES FactPurchasing(PONumber,LineNumber));
CREATE INDEX ix_sales_date_customer ON FactSales(DateKey,CustomerID);
CREATE INDEX ix_inventory_product_warehouse ON FactInventory(ProductID,WarehouseID);
CREATE VIEW MonthlySales AS SELECT d.YearMonth, SUM(f.Revenue) Revenue, SUM(f.GrossProfit) GrossProfit,
 SUM(f.Quantity) Units, COUNT(DISTINCT f.InvoiceID) Invoices FROM FactSales f
 JOIN DimDate d ON d.DateKey=f.DateKey GROUP BY d.YearMonth;

-- Canonical marts shared by dashboard transforms.
CREATE VIEW CustomerSales AS SELECT CustomerID, SUM(Revenue) LifetimeRevenue,
 SUM(GrossProfit) GrossProfit, MAX(DateKey) LastPurchaseDate, COUNT(DISTINCT InvoiceID) Orders
 FROM FactSales GROUP BY CustomerID;
CREATE VIEW VendorQuantity AS SELECT VendorID, COUNT(DISTINCT PONumber) POCount,
 SUM(OrderedQuantity) OrderedQuantity, SUM(ReceivedQuantity) ReceivedQuantity,
 SUM(OrderedQuantity*UnitCost) POValue FROM FactPurchasing GROUP BY VendorID;
CREATE VIEW InventoryBalance AS SELECT ProductID, WarehouseID, SUM(Quantity) AvailableQty
 FROM FactInventory GROUP BY ProductID, WarehouseID;
