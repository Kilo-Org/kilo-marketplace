# JOIN and KEEP Prefixes

JOIN and KEEP combine two tables. **Critical difference from SQL:** Qlik joins on ALL fields with matching names between the two tables, not just the field you intend as a key. Unintended field-name overlaps produce wrong results silently.

## Worked example of the silent collision

```qlik
// Customers has: CustomerID, Name, Status, Region
// Orders has:    OrderID, CustomerID, OrderDate, Amount, Status
// BOTH tables have a 'Status' field -- a silent collision waiting to happen.

// WRONG -- Qlik will join on BOTH CustomerID AND Status:
[Customers]: LOAD CustomerID, Name, Status, Region FROM [customers.qvd] (qvd);
LEFT JOIN([Customers])
LOAD OrderID, CustomerID, OrderDate, Amount, Status FROM [orders.qvd] (qvd);
// Result: orders only attach to customers where Status matches too.
// A customer with Status='Active' and an order with Status='Shipped'
// will NOT match. The LEFT JOIN silently drops those orders.

// RIGHT -- alias the overlapping non-key field before the join:
[Customers]:
LOAD CustomerID, Name, Status AS [Customer.Status], Region
FROM [customers.qvd] (qvd);

LEFT JOIN([Customers])
LOAD OrderID, CustomerID, OrderDate, Amount, Status AS [Order.Status]
FROM [orders.qvd] (qvd);
// Now CustomerID is the only shared field and the only join criterion.
```

**The rule:** Before any JOIN, list the fields in both tables and alias every non-key field that shares a name. Never rely on Qlik to "figure out" the intended key.

## JOIN syntax

```qlik
// LEFT JOIN adds lookup fields to the main table (rows preserved):
LEFT JOIN([Orders])
LOAD [%Customer.Key], [Customer.Region]
RESIDENT [Customers];

// INNER JOIN retains only matching rows:
INNER JOIN([Orders])
LOAD DISTINCT [%Customer.Key] RESIDENT [ActiveCustomers];
```

## JOIN vs KEEP

JOIN merges into one table (matched fields combined). KEEP filters both tables to matching rows but keeps them as separate tables in the data model. Use KEEP when you want association filtering without merging.

## Row multiplication

If the join key is not unique in both tables, rows multiply. A 1000-row fact joined to a lookup with 3 rows per key produces 3000 rows. Always ensure the lookup side has unique keys, or use ApplyMap instead.

## Decision framework

JOIN for small lookups with unique keys. ApplyMap for large lookups or when you need a default value (see SKILL.md Section 9). Let the associative engine handle dimension-to-fact relationships naturally (no join needed). See `qlik-performance` for JOIN vs ApplyMap benchmarks.
