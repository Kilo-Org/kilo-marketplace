---
name: data-investigation
description: >-
  A workflow for conducting rigorous, reproducible data investigations and
  ad-hoc analyses. This skill should be used when investigating a business
  question, explaining a metric anomaly, validating a hypothesis, performing
  root cause analysis, or preparing a one-off investigation dashboard or memo.
license: MIT
metadata:
  category: development
  author: Pedro / Kilo Code
---

# Data Investigation

Use this skill to produce investigations that are fast, correct, reproducible,
and communicate a clear conclusion rather than a pile of charts.

## Purpose

Every investigation should be answerable in one sentence before the first SQL
query is written.

## Phase 1: Frame Before Querying

### 1. Write the one-sentence answer first

Before writing any SQL, write the sentence the conclusion is expected to be.

Example: `The cohort size gap is a definition problem rather than a product behavior problem.`

If the sentence cannot be written, the question is not yet understood.

### 2. Classify the investigation type

| Type | Trigger | Approach |
|---|---|---|
| Gap analysis | Why do A and B not match? | Establish the gap, localize it, explain it |
| Root cause | Why did this metric change? | Confirm real, isolate segment, align timing, validate mechanism |
| Hypothesis test | Is X causing Y? | Define what must be true, test sub-claims, confirm or reject |
| Feasibility check | Is this number trustworthy? | Check grain, joins, nulls, definition overlap |

### 3. State 2-3 competing hypotheses before querying

Never investigate with a single hypothesis. That creates confirmation bias.

Order hypotheses by plausibility and note which one is currently expected to be
correct and why.

## Phase 2: Build Queries In Escalating Specificity

### 1. Establish first, explain second

Step 1 always confirms the anomaly is real and measures its magnitude.
Do not jump to cause until the effect is confirmed.

```sql
select
    <time_bucket>,
    <source_a_count> as metric_a,
    <source_b_count> as metric_b,
    <source_a_count> - <source_b_count> as gap,
    round(100.0 * (<source_a_count> - <source_b_count>) / nullif(<source_a_count>, 0), 1) as pct_gap
from ...
order by 1
```

### 2. Localize by breaking one dimension at a time

After confirming the gap, break it down along one dimension per step:
- By time: when did it appear?
- By segment: who is affected?
- By signal/source: which path is missing?

### 3. Align timing with upstream changes

Once the anomaly start date is known, check:
- git commits to relevant models, ETL jobs, or application code
- schema migrations or source changes
- metric definition changes
- external events such as launches, campaigns, or pricing changes

A credible root cause must explain why the metric changed when it did.

### 4. Validate the mechanism

After identifying a candidate cause, confirm it mechanically:
- Does the affected population match the predicted population?
- What does the counterfactual look like?
- Does a second independent signal support the explanation?

Do not stop at correlation.

### 5. Quantify each hypothesis before concluding

For every candidate explanation, produce a number.

Examples:
- `H1 accounts for 1,240 users`
- `H2 accounts for 1,050 users`

If a hypothesis cannot be quantified, it is not yet validated.

## Phase 3: SQL Hygiene Rules

### Use stable time bounds for investigations

Investigation SQL should be reproducible. Favor fixed bounds over rolling
windows unless the analysis is intentionally operational and evergreen.

```sql
-- Prefer fixed investigation scope
where created_at >= '2026-02-16'
  and created_at < '2026-04-04'
```

### Add explicit grain comments in important CTEs

```sql
-- grain: one row per user
with first_instances as (
    select user_id, min(created_at::date) as first_instance_date
    from ...
    group by 1
)
```

### Always `NULLIF` denominators

```sql
round(100.0 * numerator / nullif(denominator, 0), 1)
```

### Test definition overlap before comparing counts

When two counts should match but do not, verify:
1. Same grain?
2. Same population?
3. Same time window?
4. Same business definition?

Definition mismatches are one of the most common causes of fake anomalies.

## Phase 4: Dashboard Structure

### One explanation block per step

Each chart or tile group should answer one question and state the finding in
plain language.

Example:

```markdown
## How severe is the gap, and when did it start?

The gap stayed below 7% through the baseline period, then jumped to 31% in the
week of Mar 23. The abruptness argues against slow data drift.
```

The reader should be able to understand the investigation from the prose alone.
Charts should prove the conclusions, not carry them alone.

### Pair absolute and percentage views

For any gap or composition analysis:
- Left: absolute counts
- Right: percentages or rates

### End with a conclusions block

Always finish with:
1. Root cause in one sentence
2. Hypotheses eliminated and why
3. Recommended action, if any

## Phase 5: Handoff Spec

When the investigation will be turned into a dashboard, memo, or follow-up
analysis, prepare a handoff spec.

Suggested structure:

```markdown
## Section N - [Title]

### Query
[Final SQL]

### Results
[Representative result sample]

### Finding
[1-3 sentences describing what this proves]

### Presentation
Chart type: <line / bar / table / paired charts>
X axis: COLUMN_NAME
Series: COLUMN_NAME(S)
Color: COLUMN_NAME (if applicable)
```

End with:

```markdown
## Conclusions

Root cause: [...]
Hypotheses confirmed: [...]
Hypotheses eliminated: [...]
Recommended action: [...]
```

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Confirmation bias | Force at least one disconfirming test for each hypothesis |
| Stopping at correlation | Add mechanism and timing validation |
| Skipping grain checks | State and verify grain early |
| Mixing investigation and production logic | Keep one-off analysis separate unless promoted intentionally |

## Keywords

data investigation, root cause analysis, metric anomaly, hypothesis testing,
gap analysis, reproducible SQL, investigation dashboard
