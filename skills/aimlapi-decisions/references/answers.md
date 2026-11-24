# Reading answers

A `200` from `/v1/decisions` has `model` (the provider's name for the version that answered, such as `jev-1.14.0`: do not compare it with the id you sent), `answers`, `usage` and `meta` (`meta.model`, `meta.usage` with the cost of this call). Read each answer by its `type`.

## System One answers

`answers` is an object with one entry per question key.

| `type` | Fields | How to read it |
| ------ | ------ | -------------- |
| `noul` | `noul` | probability of "yes", 0 to 1 |
| `choice` | `choice`, `confidence`, `probabilities` | `choice` is the likeliest key; `probabilities` has every key and sums to 1; `confidence` is the model's calibrated confidence that `choice` is right, which need not equal the top probability |
| `choice` with `multiple: true` | `choices`, `probabilities` | `choices` lists every option at 0.5 or above; each probability is that option's own and they need not sum to 1 |
| `score` | `score`, `confidence`, `probabilities`, `legend` | `score` is the expected level index from 0 (for example `1.21`), `probabilities` is keyed by level index, `legend` maps index to the level you sent |
| `text`, `date` | value, `text`, `span`, `found` | `found` is the probability the value is in the state; when it is not, the value, `text` and `span` are `null`. `date` is ISO 8601 |
| `number` | `number`, `unit`, `text`, `span`, `found` | read as written, not converted ("1 234,50 EUR" is `1234.5` in `EUR`). With `range`: `number` is the median and `interval` the 10th to 90th percentile, no `found` |
| `spans` | `spans[]` (`text`, `span`, `found`), `count`, `presence`, `at_least` | `at_least: true` means every slot was used: raise `max` and ask again |
| `box` | `box` (`top`, `bottom`, `left`, `right`), `confidence`, sometimes `found` | edges are fractions of the image from its top-left corner. Where the answer has no `found`, a box always comes back: ask a `noul` "is it there" next to it |
| `boxes` | `boxes[]`, `count`, `presence`, `at_least` | as `spans`, for objects in the image |

Some published response schemas list only `noul`, `choice`, `score` and `box`; the other types still answer in the shapes above (checked in sandbox mode for `date`, `number` and `choice` with `multiple`).

## OpenAI Decisions answers

`answers` is an array in the order of `questions`, each with the question's `name`.

| `type` | Fields |
| ------ | ------ |
| `predicate` | `probability` that the condition is true |
| `choice` | `choice` (a `value`), `confidence`, `probabilities: [{value, probability}]` |
| `score` | `score` (expected level index from 0), `confidence`, `probabilities: [{value, label, probability}]` |
| `refusal` | the model declined this question: treat it as no answer |

`usage` here also has `total_tokens` and may have `input_tokens_details`.

## Turning probabilities into decisions

- Calibrated means that across many answers, those given 0.8 are right about 80% of the time. One answer at 0.8 is still wrong one time in five.
- Pick the threshold from what a mistake costs. A moderation gate that must not miss abuse blocks at a low probability; a gate that must not block good users blocks only at a high one. Measure both error rates on 100 or more labelled examples from the user's data, per model; a threshold tuned on one model does not carry to another.
- Keep three outcomes where it helps: act above a high bar, reject below a low bar, send the middle to a person or a stronger model.
- For a `choice`, gate on `confidence` when the question is "is the pick right"; gate on one option's probability when the question is about that option ("is it billing, with at least 0.9").
- For a `score`, `round(score)` is the nearest level, but a cut such as "angry or worse" is the sum of `probabilities` for those levels.
- Store the probability next to the decision, so the threshold can be moved later without asking again.

## Parser (Python)

```python
def read_answers(body: dict) -> dict:
    """Return {question name: answer dict} for either response shape."""
    answers = body["answers"]
    if isinstance(answers, list):  # OpenAI Decisions shape
        return {a["name"]: a for a in answers}
    return dict(answers)  # System One shape


def yes(answer: dict):
    """Probability of yes for noul or predicate, None for other types."""
    if answer["type"] == "noul":
        return answer["noul"]
    if answer["type"] == "predicate":
        return answer["probability"]
    return None


def option_probability(answer: dict, option: str) -> float:
    probs = answer.get("probabilities") or {}
    if isinstance(probs, list):  # OpenAI Decisions shape
        return next((p["probability"] for p in probs if p.get("value") == option), 0.0)
    return probs.get(option, 0.0)
```

Check `answer["type"]` before reading a field: a `refusal`, or a `null` value with a low `found`, is a normal answer, not an error.

## Cost

Read the rates from `GET /v1/models?type=internal/decisions&include=pricing`. Decision models list two token units: input (`origin: provided`) at the model's rate and output (`origin: generated`) at `0`. Divide `price` by `per`. A model with `pricing.kind: variable` is billed by what the provider reports, so read the cost after the call.

What grows the input count:

| Input | Effect |
| ----- | ------ |
| `state` and every question's text | counted once per request |
| images, video frames, audio | input tokens; the field description gives the rate (for example 1.5 tokens per 32 × 32 patch). Where it says "again for every question", ten questions about one image pay for it ten times |
| `spans`, `boxes` slots | where the description says so, every slot is billed, filled or not |

The cost of each call is in the `x-aimlapi-usd-spent` and `x-aimlapi-credits-used` headers and `meta.usage`; totals in `/v2/logs` (`aimlapi-costs`).
