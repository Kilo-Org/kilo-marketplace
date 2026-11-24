---
name: aimlapi-decisions
description: >-
  Use when classifying, routing, moderating, triaging, scoring or extracting
  values from content with AI/ML API (aimlapi) decision models on /v1/decisions
  (Jev, d1, HeyGen or Gemini Decision), reading their calibrated probabilities,
  choosing a decision threshold, or calling a router such as
  aimlapi/dynamic-router, typesafe/jev-router or liquid/d1-router and reading
  meta.router.
compatibility: >-
  Needs network access to api.aimlapi.com and AIMLAPI_API_KEY in the
  environment. The script needs python3 and no key.
metadata:
  version: 1.0.5
  docs: 'https://docs.aimlapi.com/api-references/decision-models.md'
  category: development
  source:
    repository: 'https://github.com/aimlapi/skills'
    path: skills/aimlapi-decisions
    license_path: LICENSE
    ref: v1.0.5
    commit: e65990f10f38fdf278b404a17b27266718788517
---

# Ask decision models, and route with them

A decision model writes no text: `POST /v1/decisions` returns one typed answer per question, with probabilities. A router is a model id on the usual endpoints whose decision model picks the bucket of models that answers.

## When to use

- "Is this spam / urgent / safe", "which team gets this ticket", "rate this answer 1 to 5"
- Replacing an LLM judge or JSON classifier
- Reading a date, number or personal data out of text, or finding an object in an image
- Easy prompts to a cheap model, hard ones to a strong one; spam stopped before any model runs

Free-text answers and tool calls: `aimlapi-chat`.

## Steps

### 1. Pick a model and read its shape

Ids and prices come from the catalogue, never memory:

```bash
curl -s 'https://api.aimlapi.com/v1/models?type=internal/decisions&include=pricing'
python3 scripts/decide.py shape typesafe/jev
```

`shape` prints what `info.docsJson` allows. Two shapes share the endpoint; the wrong one is a `400`:

| Shape | Content | Questions | Yes/no type |
| ----- | ------- | --------- | ----------- |
| System One (most models) | `state` | object keyed by your names | `noul` |
| OpenAI Decisions | `input` | array of items with `name` | `predicate` |

Question types and media differ by model: [references/shapes.md](references/shapes.md).

### 2. Ask

```bash
curl -s https://api.aimlapi.com/v1/decisions \
  -H "Authorization: Bearer $AIMLAPI_API_KEY" -H 'Content-Type: application/json' -d '{
  "model": "typesafe/jev",
  "state": "Help! My payments have been failing for 3 days and nobody answers support.",
  "questions": {
    "is_urgent": {"type": "noul", "instructions": "Does this convey urgency?"},
    "department": {"type": "choice", "instructions": "Which team should handle this?",
      "criteria": {"billing": "Payments, invoicing, refunds", "technical": "Bugs, outages, integrations"}},
    "frustration": {"type": "score", "instructions": "How frustrated is the customer?",
      "criteria": ["Calm", "Frustrated", "Very angry"]}}}'
```

### 3. Read the answer

Each question key comes back under `answers` (System One), or each item in order with its `name` (OpenAI shape).

- `noul` is the probability of "yes", 0 to 1; your code picks the threshold.
- `choice` is the likeliest key, `probabilities` covers every key, `confidence` is the calibrated confidence in that choice.
- `score` is the expected level index from 0, often fractional, not a probability.
- Extraction answers carry `found`; a missing value is `null`.

All answer types and a parser: [references/answers.md](references/answers.md).

### 4. Route

```bash
curl -s https://api.aimlapi.com/v1/chat/completions \
  -H "Authorization: Bearer $AIMLAPI_API_KEY" -H 'Content-Type: application/json' -d '{
  "model": "aimlapi/dynamic-router",
  "messages": [{"role": "user", "content": "WINNER!! Claim your prize: call 09061701461."}],
  "router": {"decision_model": "typesafe/jev-1.14", "default_bucket": "answer", "buckets": [
    {"name": "spam", "when": "Unsolicited adverts, prizes to claim, premium-rate numbers, phishing", "models": []},
    {"name": "answer", "when": "Anything else", "models": ["openai/gpt-4o-mini"]}]}}'
```

Read `meta.router` (in a stream, on the last chunk): `bucket`, `reason`, `routed`, `choice`, `confidence`, `judgement.credits`. A bucket with `models: []` ends the request with an empty answer and `routed: false`. A failed judgement is not an error: the request goes to `default_bucket` with a `classifier_*` reason. Allowed decision models: `python3 scripts/decide.py judges`. More: [references/routers.md](references/routers.md).

### 5. Price and test

Decision models charge input tokens, media included; a router adds the judgement to the answering model's charge ([answers](references/answers.md#cost), [routers](references/routers.md#cost)).

Test bodies free with the header `X-AIMLAPI-Sandbox: 1` (`aimlapi-sandbox`): it validates against the schema; probabilities are fixed. For routers the sandbox neither checks `router` nor returns `meta.router`: test that live, once, small.

## Rules

- [ ] Read the shape from `docsJson` before writing a body; one model's fields do not fit another.
- [ ] Never hard-code a model list, price or limit in the user's code; read them from the catalogue or config.
- [ ] Set thresholds on labelled examples of the user's data; log the probability with the decision.
- [ ] Give a `choice` a "none of these" option when the options may not cover every input.
- [ ] Bucket `models` take models that answer; a decision model goes only in `decision_model`.

## Errors

| Response | Do |
| -------- | -- |
| `400` "Validation failed", `error.details[].path` | fix that field (step 1) |
| `400`, `details[].path` in `images` or `assets` | outside the model's limits (never resized): follow `reason` |
| `400` "Invalid router configuration: router..." | fix the field it names; `decide.py judges` |
| `403 model_not_allowed` | the key does not allow a model, including one named inside `router` |
| `meta.router.reason` `classifier_*` | the judgement failed; make `default_bucket` the safe bucket |
| `429`, `5xx` | `aimlapi-errors` |

## Check before done

- [ ] Each body got a sandbox `200` with the expected answer keys.
- [ ] Code reads answers by `type` and handles `null` and `found`.
- [ ] Router code acts on `meta.router.bucket` and treats `routed: false` as a decision.
- [ ] Any price quoted came from `include=pricing` just now.

## Reference

- [references/shapes.md](references/shapes.md): request shapes, question types, media
- [references/answers.md](references/answers.md): answer types, thresholds, parser, cost
- [references/routers.md](references/routers.md): router fields, `meta.router`, ladders, cost
- Docs: https://docs.aimlapi.com/api-references/decision-models.md
