# Scraping Guide

Use scraping for structured records from supported platforms, not as a generic page fetcher. Fetch ordinary or unsupported pages directly.

> **Reference**: [scrape.datasets.md](../api-reference/scrape.datasets.md) — curated datasets and exact input shapes

## Dataset and mode selection

1. Consult the curated reference. For a specific page, choose the stable URL-collector dataset; for search results, feeds, profile posts, categories, or hashtags, choose the matching `*_by_*` discovery dataset.
2. If no curated choice supports the requested mode, use `scrape search` with the platform plus data type. Its raw `gd_` result includes collector inputs and discovery modes.
3. For a raw `gd_` discovery mode, pass its `discoverBy` value and exactly that mode's input fields. Preserve field names and JSON types; similar datasets often use different names such as `keyword`, `keywords`, or `search_keyword`.

Batch inputs only when they share a dataset ID and mode. Keep the default `--limit-per-input` (10) unless the user asks for more: every returned record is billed. Credits for inputs × limit are held while the scrape runs, so pass `--limit-per-input 1` when each input is a single page (a profile, product page, single post, or video). One call may not exceed 1000 records (inputs × limit); split larger jobs.

```bash
teable scrape search --query "glassdoor company reviews"
teable scrape run --dataset-id gd_XXXX --discover-by keyword --inputs '[{"keyword":"database engineer","location":"Berlin"}]' --limit-per-input 20
```

## Asynchronous results

`teable scrape run` starts the job and immediately returns a snapshot ID. Retain it and fetch the result with status polling; a wait of up to 120 seconds can reduce repeated calls.

```bash
teable scrape status --snapshot-id s_XXXX --wait 60
```

If the status remains pending, repeat **status** with the same snapshot ID. Never rerun `scrape run` for the same inputs: that starts and bills a second job rather than resuming the first.
