# Live speed: `GET /models/metrics`

Source: https://docs.aimlapi.com/api-references/service-endpoints/model-metrics.md

No key. Percentiles over a short sliding window (`window_seconds`, a few minutes), measured on successful requests only. Filter with `aliases`, repeated once per model: `?aliases=openai/gpt-4o-mini&aliases=google/gemini-2.5-flash-lite` (a comma-separated list matches nothing; any other query parameter is a `400`).

```json
{
  "window_seconds": 300,
  "generated_at": "2026-11-23T09:26:33.742Z",
  "models": [
    {
      "alias": "openai/gpt-4o-mini",
      "endpoint": "openai/chat-completions",
      "metrics": {
        "ttft_ms": {"p50": 599, "p75": 1248, "p90": 1248, "p99": 1248},
        "tps": {"p50": 31.25, "p75": 63.19, "p90": 80.26, "p99": 99.94},
        "duration_ms": {"p50": 1012, "p75": 3549, "p90": 7428, "p99": 194496}
      }
    }
  ]
}
```

| Field | Means | Read it as |
| ----- | ----- | ---------- |
| `ttft_ms` | time to first token, streaming text models | lower is better; p90 and p99 are the slow tail |
| `tps` | output tokens per second | **higher is better**; p99 is the fastest requests, p50 the typical one |
| `duration_ms` | whole request | lower is better; depends on answer length, so compare models on the same kind of task |

- A model missing from `models` had no successful request in the window: no data, not zero latency. A model failing every request drops off the list too.
- One window is a few minutes of traffic. For a decision, read it a few times, and compare p50 and p90, not one p99.
- Speed is one input. Shortlist by capability and price first (SKILL.md steps 1 to 4), then pick between models that are otherwise interchangeable.
