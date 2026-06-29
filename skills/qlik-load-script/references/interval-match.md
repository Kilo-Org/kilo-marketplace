# IntervalMatch Prefix

`IntervalMatch` is the script prefix for linking a **discrete numeric value** (a point) to one or more **intervals** (low/high pairs) loaded from a separate table. Use it whenever the lookup is "which interval contains this value?" rather than "what value does this key map to?"

Canonical use cases: SCD Type 2 effective-dating (`effective_from` / `effective_to`), Data Vault 2.0 satellite point-in-time lookups, version-history reconstruction, time-of-day shift / production-window matching, and any dimensional lookup where the interval table can change over time without a code change.

This page covers what `IntervalMatch` does, its synthetic-key behaviour and the standard resolution, multi-key form, an SCD2 worked example, performance notes, and an explicit "when to use which" decision block versus the range-bucketing-via-`ApplyMap` pattern in `qlik-load-script` SKILL.md Section 7.

> **Tier-1 sources**
> - IntervalMatch prefix: https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptPrefixes/IntervalMatch.htm
> - ApplyMap function: https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/MappingFunctions/ApplyMap.htm
> - Join / Keep prefixes: https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptPrefixes/Join.htm
> - Drop Table statement: https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Scripting/ScriptRegularStatements/Drop_Table.htm

---

## 1. Syntax

**One-key form** — match a single point field against an interval table:

```qlik
IntervalMatch (matchfield) (loadstatement | selectstatement)
```

`matchfield` is the already-loaded discrete field. The `LOAD`/`SELECT` that follows must return the interval lower limit as the **first** column and the upper limit as the **second** column.

**N-key form** — up to five extra key fields filter the match (e.g., match by date AND product line):

```qlik
IntervalMatch (matchfield, keyfield1 [, keyfield2, ... keyfield5]) (loadstatement | selectstatement)
```

In the N-key form the `LOAD` must return: `low, high, keyfield1, keyfield2, ...` in that order. Match succeeds only when the point falls inside the interval **and** every key field value matches the corresponding row.

### Per Tier-1: closed intervals, overlap allowed, NULL bounds

The help.qlik.com IntervalMatch page documents three behaviours explicitly:

1. **Intervals are always closed** — both endpoints are included. There is no "open" or "half-open" mode and no `USING` clause for boundary control. If you need an exclusive boundary, subtract one second/day from the upper bound (or add to the lower) before the match.
2. **Overlapping intervals are allowed and supported** — a point that sits inside two intervals will be linked to both. The output row count multiplies accordingly. If overlap is unintended, fix the source data rather than relying on `IntervalMatch` to pick one.
3. **NULL interval bounds are silently disregarded** — a row with a NULL lower or upper limit is dropped from the match. SCD2 sources commonly store the still-current row's `effective_to` as NULL. Convert it to a safe far-future sentinel before the match (see Section 4).

---

## 2. The Synthetic Key — Why It Appears, How to Resolve It

`IntervalMatch` produces an output table whose key columns are **every field** from the interval `LOAD` plus the matchfield. The matchfield already exists in the original fact table. In the N-key form, the keyfields exist in the fact table too. Result: the output table shares **two or more field names** with the fact table, which by Qlik's one-key rule is a synthetic key — Qlik creates a `$Syn` table with solid connector lines linking them. (Synthetic-key concepts live in `qlik-data-modeling` Section 2 and `references/anti-patterns.md` #1.)

The standard resolution is `LEFT JOIN` the IntervalMatch output back into the fact table, then `DROP` the now-empty IntervalMatch table:

```qlik
// 1. Fact table — already loaded, contains the point field [Event.Time]
[EventLog]:
LOAD * INLINE [
Event.Time, Event, Comment
00:00, 0, Start of shift 1
01:18, 1, Line stop
02:23, 2, Line restart 50%
04:15, 3, Line speed 100%
];

// 2. Interval source — low, high, plus whatever attributes you want to attach
[OrderLog]:
LOAD * INLINE [
Order.Start, Order.End, Order
01:00, 03:35, A
02:30, 07:58, B
03:04, 10:27, C
];

// 3. IntervalMatch into a NAMED table -- DO NOT leave it anonymous
[_IM_EventOrder]:
IntervalMatch ([Event.Time])
LOAD Order.Start, Order.End RESIDENT [OrderLog];

// 4. LEFT JOIN the IntervalMatch output back onto the fact -- this collapses
//    the synthetic key by moving the interval columns into [EventLog]
LEFT JOIN ([EventLog]) LOAD * RESIDENT [_IM_EventOrder];

// 5. Drop the intermediate table -- the $Syn disappears with it
DROP TABLE [_IM_EventOrder];

// 6. Attach the Order attributes via a normal association on [Order]
//    (or LEFT JOIN them in too, depending on cardinality)
```

The `LEFT JOIN` is performed on the matching fields between `[EventLog]` and `[_IM_EventOrder]` — by construction this is `Event.Time` (the matchfield) plus `Order.Start` and `Order.End` (the interval bounds), which only exist in `[_IM_EventOrder]`. So the effective join key is `Event.Time`, every event row gets the matched interval columns attached, and dropping the IntervalMatch table removes the synthetic key.

> **Folklore correction.** The synthetic key from `IntervalMatch` is structural — it appears every time the prefix is used. It is **not** a bug or a "first-time-setup quirk." The `LEFT JOIN` + `DROP TABLE` step is mandatory, not optional. Do not ignore the `$Syn` and ship the model.

---

## 3. N-Key Form — Multi-Field Matching

Use the N-key form when the interval is qualified by additional dimensions. The classic example is **per-line** production schedules — the same wall-clock interval applies to Line A but a different interval applies to Line B:

```qlik
[OrderLog]:
LOAD * INLINE [
Start, End, ProductionLine, Order
01:00, 03:35, A, OrdA-1
02:30, 07:58, A, OrdA-2
03:04, 10:27, B, OrdB-1
];

[_IM]:
IntervalMatch ([Event.Time], ProductionLine)
LOAD Start, End, ProductionLine RESIDENT [OrderLog];

LEFT JOIN ([EventLog]) LOAD * RESIDENT [_IM];
DROP TABLE [_IM];
```

Per Tier-1, up to five extra key fields are supported. Every key field listed in the `IntervalMatch(...)` argument must also appear in the `LOAD` statement.

---

## 4. SCD Type 2 Effective-Dating Worked Example

The pattern: a dimension table stores `effective_from` / `effective_to` per version of each business entity, and the fact table records a transaction date. The lookup is "which version of customer X was in force on the transaction date?"

```qlik
// 1. Fact -- one row per order, with a single transaction date
[Orders]:
LOAD * INLINE [
Order.ID, Customer.BusinessKey, Order.Date, Order.Amount
1001,     C-100,                2025-01-15,  500.00
1002,     C-100,                2025-04-20,  750.00
1003,     C-200,                2025-03-10,  100.00
] (delimiter is ',');

// 2. SCD2 dimension -- multiple versions per business key.
//    NOTE: the still-current row has NULL effective_to in the source,
//    which IntervalMatch would silently disregard. Substitute a far-future
//    sentinel BEFORE the match.
[Customer_History]:
LOAD
    Customer.BusinessKey,
    Customer.Tier,
    Date#(Customer.EffectiveFrom, 'YYYY-MM-DD') AS Customer.EffectiveFrom,
    IF(IsNull(Customer.EffectiveTo) OR Len(Trim(Customer.EffectiveTo)) = 0,
       MakeDate(9999, 12, 31),
       Date#(Customer.EffectiveTo, 'YYYY-MM-DD')) AS Customer.EffectiveTo
INLINE [
Customer.BusinessKey, Customer.Tier, Customer.EffectiveFrom, Customer.EffectiveTo
C-100,                Silver,        2024-01-01,              2025-03-31
C-100,                Gold,          2025-04-01,
C-200,                Bronze,        2024-06-01,
] (delimiter is ',');

// 3. IntervalMatch on the transaction date, qualified by business key
[_IM_Customer]:
IntervalMatch (Order.Date, Customer.BusinessKey)
LOAD Customer.EffectiveFrom, Customer.EffectiveTo, Customer.BusinessKey
RESIDENT [Customer_History];

// 4. Collapse the synthetic key into the fact
LEFT JOIN ([Orders]) LOAD * RESIDENT [_IM_Customer];
DROP TABLE [_IM_Customer];

// 5. Attach the version attributes (Customer.Tier) from Customer_History
//    via a normal association on the composite of business key + effective dates
//    -- already in [Orders] after the LEFT JOIN, so the association is automatic
```

After the `LEFT JOIN`, every order row carries the matching `Customer.EffectiveFrom` and `Customer.EffectiveTo` for the version that was in force on `Order.Date`. Order 1001 (2025-01-15) gets the Silver row's interval; Order 1002 (2025-04-20) gets the Gold row's interval; Order 1003 (2025-03-10) gets the Bronze row's interval.

**Boundary check.** Per Tier-1 the intervals are closed, so a transaction date that falls exactly on `effective_from` AND on the previous row's `effective_to` will match both. SCD2 sources should not produce overlapping closed windows — if yours does, decrement the prior `effective_to` by one day on load:

```qlik
Customer.EffectiveTo - 1 AS Customer.EffectiveTo   // half-open emulation
```

---

## 5. Performance Notes

- **Row multiplication.** `IntervalMatch` produces one output row per (point, interval) match. Overlapping intervals multiply rows. A 10M-row fact matched against a dimension with 2 overlapping versions per key doubles to 20M rows. Audit row count immediately after the match.
- **Force standard QVD read.** The interval table is typically built from a `RESIDENT` load, but if you `IntervalMatch` directly against a QVD using a `WHERE` clause or a transform on the bounds, you force standard read mode. Pre-load the interval table into RESIDENT first, then `IntervalMatch` against it. See `qlik-load-script` SKILL.md Section 10.
- **Small interval tables are cheap; large ones are not.** The match is an O(facts × intervals) scan, not an index lookup. With 10M facts and a 100-row interval table, the match is fast. With 10M facts and a 1M-row interval table (e.g., a per-customer SCD2 history across millions of customers), expect noticeable load time. Mitigate by partitioning the fact load and matching per partition, or by collapsing the SCD2 dimension to current-version-only if the historical view is not needed.
- **Multi-key form does not change the algorithmic shape.** It adds equality filtering inside the scan, not an index. With 5 key fields the per-row comparison is more expensive than with 1.

---

## 6. When to Use Which: IntervalMatch vs Range Bucketing (ApplyMap)

The Range Bucketing via mapping expansion pattern in `qlik-load-script` SKILL.md Section 7 expands an interval definition into one mapping row per discrete integer in the range, then resolves with `ApplyMap`. It looks like it could replace `IntervalMatch` for any range lookup. It cannot. They solve different problems.

| Signal | Use `IntervalMatch` | Use Range Bucketing (`ApplyMap`) |
|---|---|---|
| Interval source is **time-varying** (SCD2 history, DV2 satellite versions, audit/version table) | Yes | No — the expansion would have to re-run on every change |
| Intervals are **data-driven** (one row per business entity, different bounds per entity) | Yes | No — `ApplyMap` is one global lookup table, not entity-qualified |
| You need **multi-key matching** (date + product line, date + business key) | Yes — N-key form | No — `ApplyMap` is single-key |
| Bounds are **non-integer** (timestamps, decimals, money tiers) | Yes — `IntervalMatch` is numeric-aware | No — the expansion enumerates integers via `WHILE IterNo()`, so it requires integer bounds |
| Buckets are **static and enumerable** (age bands 0-17, 18-24, ...; price tiers; star ratings) | Optional | Yes — simpler, faster, no synthetic-key step |
| Bucket set is **small** (≤ ~1000 mapping rows after expansion) | Optional | Yes |
| Bucket set is **large or sparse** (e.g., a 100-year date range expanded daily = ~36500 rows per entity per key) | Yes | No — expansion explodes the mapping table |
| You want **overlapping match** (one point may match multiple ranges) | Yes — `IntervalMatch` returns all matches | No — `ApplyMap` returns one value |
| You want **a default value** for unmatched points | Optional — use NULL handling | Yes — `ApplyMap('map', x, 'Default')` |
| You want to **edit bucket definitions** by changing an INLINE table | Optional | Yes — that's the pattern's purpose |

**Rule of thumb.** If the interval table looks like a **dimension** (one row per business entity, attributes vary over time), use `IntervalMatch`. If the interval table looks like a **reference list** (bucket definitions that apply globally to every entity), use Range Bucketing.

---

## 7. Wrong-Choice Scenarios

Three cases where picking the wrong pattern silently produces wrong results.

### Scenario A — Age bands. Range Bucketing is correct; IntervalMatch is overkill.

A patient's age in years (integer) is matched to a static set of age bands (0-17, 18-24, 25-34, ...). The bands never vary by patient — they are a global reference list.

- **Range Bucketing with `ApplyMap`** — one INLINE table defines the bands, the expansion produces ~200 mapping rows (one per integer year, 0-200), `ApplyMap` is an O(1) symbol-table lookup at LOAD time. No synthetic key, no `LEFT JOIN` cleanup, no row multiplication.
- **`IntervalMatch`** — works but adds a synthetic key that must be resolved, and the match is O(facts × bands) instead of O(facts). Wrong tool — slower, more code, no upside.

### Scenario B — Customer SCD2 history. IntervalMatch is correct; Range Bucketing is broken.

A customer's tier (Silver / Gold) changes over time and each version has an `effective_from` / `effective_to`. Different customers have different versions and different effective dates. A fact table records orders by `Customer.BusinessKey` and `Order.Date`.

- **`IntervalMatch (Order.Date, Customer.BusinessKey)`** — correctly matches each order to the customer version in force on the order date. See the Section 4 worked example.
- **Range Bucketing with `ApplyMap`** — `ApplyMap` is one global key→value table, so it cannot represent "Customer C-100's tier from 2024-01-01 through 2025-03-31 was Silver; from 2025-04-01 onward is Gold; Customer C-200's tier from 2024-06-01 onward is Bronze." There is no key that uniquely identifies a (customer, date) pair short of pre-computing the entire customer × date Cartesian product — which is exactly what `IntervalMatch` does internally for you. Building the global mapping yourself would mean expanding ~365 days × N customers rows per year. At 10K customers × 5 years that is ~18M mapping rows for a problem that `IntervalMatch` handles with the original SCD2 dimension table unchanged. Wrong tool — incorrect at small scale, infeasible at scale.

### Scenario C — Price tiers per product line. IntervalMatch is correct because the tiers are data-driven.

Different product lines have different price-tier definitions (Line A: 0-99 Bronze, 100-499 Silver, 500+ Gold; Line B: 0-49 Bronze, 50-249 Silver, 250+ Gold). A fact table records sales by `ProductionLine` and `Sale.Price`.

- **`IntervalMatch (Sale.Price, ProductionLine)`** — N-key form correctly matches each sale to the tier definition for its production line.
- **Range Bucketing with `ApplyMap`** — there is no single global price → tier mapping because the same price (say, $200) is Silver on Line A but Bronze on Line B. You would have to build a composite key (`ProductionLine & '|' & Price`) and pre-expand the mapping for every (line, price) combination. At 50 product lines × 1000 price points, that is 50K mapping rows for a problem that `IntervalMatch` solves with the original 6-row tier definition table. Wrong tool — works in principle but explodes the mapping table.

---

## 8. Quick Checklist Before Shipping

- [ ] Interval `LOAD` returns `low, high, [key1, ...]` in that order
- [ ] NULL upper bounds (still-current SCD2 rows) substituted with a far-future sentinel **before** the match
- [ ] Match-by-discrete-integer (age, score) — confirm Range Bucketing isn't the simpler fit
- [ ] IntervalMatch output table is **named** (e.g., `[_IM_Customer]`)
- [ ] `LEFT JOIN` collapses the IntervalMatch table back into the fact
- [ ] `DROP TABLE [_IM_...]` after the join — the `$Syn` should disappear from the data model viewer
- [ ] Post-match row count audit: `Sum(rows after) <= Sum(facts × max overlap)`; investigate any unexpected multiplication
- [ ] If overlapping closed windows occur in SCD2 source, decrement prior `effective_to` by 1 day to emulate half-open
