---
name: jobvetta-jobs
description: Search 6.5M+ live verified employer career-site job postings across 242 countries, inspect company hiring velocity signals, and compute market salary benchmarks via the Jobvetta API.
---

# Jobvetta Jobs & Hiring Signals

Query live, deduplicated employer career-site job postings across 238,000+ companies in 242 countries, inspect B2B company hiring velocity, and benchmark P25/median/P75 salaries using the Jobvetta REST API (`https://api.jobvetta.com/v1`).

## When to Use This Skill

- Searching active employer job openings by role keyword, location, remote status, or posting recency
- Enriching B2B target accounts with live open headcount and department hiring velocity
- Benchmarking P25, median (P50), and P75 base salaries from disclosed compensation data

## What This Skill Does

1. **Job Search**: Queries `/v1/jobs`, `/v1/jobs/remote`, and `/v1/jobs/recent` with role, location, and recency filters.
2. **Company Hiring Signals**: Queries `/v1/companies/{company}/jobs` to inspect active headcount expansion at any employer.
3. **Salary Benchmarking & Job Hydration**: Computes live percentiles via `/v1/jobs/salary-estimate` and retrieves full 70+ field job requirements via `/v1/jobs/{job_id}`.

## How to Use

Generate a free API key (`25` calls/day, no credit card required) at `https://www.jobvetta.com/api` and export `JOBVETTA_API_KEY=jvk_...`.

### Basic Usage

```bash
curl -fsSL "https://api.jobvetta.com/v1/jobs?q=Senior+Data+Engineer&location=United+States&days=7&limit=10" \
  -H "Authorization: Bearer $JOBVETTA_API_KEY"
```

### Advanced Usage

```bash
# Company hiring velocity for Datadog Security roles
curl -fsSL "https://api.jobvetta.com/v1/companies/Datadog/jobs?q=Security&limit=25" \
  -H "Authorization: Bearer $JOBVETTA_API_KEY"

# P25 / Median / P75 salary benchmark
curl -fsSL "https://api.jobvetta.com/v1/jobs/salary-estimate?q=Staff+Software+Engineer&location=United+States&days=30" \
  -H "Authorization: Bearer $JOBVETTA_API_KEY"
```

## Example

**User**: "Check how many open jobs Datadog has right now and what the median US Data Engineer salary is."

**Output**:
```json
{
  "company": "Datadog",
  "total_open_jobs": 584,
  "us_data_engineer_salary_median_usd": 154750
}
```
