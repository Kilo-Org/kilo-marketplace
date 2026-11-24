# Routers

A router is a model id you send as `model`. For each request a decision model reads the request (its text and images) and picks the bucket whose `when` fits it best; the first model in that bucket that can take the request answers, and the next one takes over if it fails. Find routers in the catalogue and read their schema, which is the authority for every field below:

```bash
curl -s 'https://api.aimlapi.com/v1/models?type=openai/chat-completions' | grep -o '"id":"[^"]*router[^"]*"'
python3 scripts/decide.py judges aimlapi/dynamic-router
```

| Kind | Example id | Decision model |
| ---- | ---------- | -------------- |
| Configurable | `aimlapi/dynamic-router` | your `router.decision_model`, from the enum in its schema |
| Preset | `typesafe/jev-router`, `liquid/d1-router` | fixed, named after the router: leave `decision_model` out, or send the same `router` to the configurable one to choose |

A router id is listed once per endpoint type it serves: `/v1/chat/completions`, `/v1/responses`, `/v1/messages`, `/v1/images/generations`, `/v1/images/edits` and `/v2/video/generations`. The same `router` object works on each; a request uses the bucket's models of its own kind. Without `router`, a router uses its default buckets, which route conversations only; image and video requests need your own buckets. The default buckets and their models are in the `router.buckets` description of the schema.

Not every decision model can judge for a router: only those in the `router.decision_model` enum. A decision model is never a bucket model, and a router is never a bucket model.

## The `router` object

| Field | Meaning |
| ----- | ------- |
| `decision_model` | which decision model judges (configurable router only) |
| `buckets` | 1 to 10 of `{name, when, models}`. `name`: letters, digits, `-`, `_`, `.`. `when`: what requests this bucket takes, in plain words; required when there are two or more buckets. `models`: models to try in order, or `[]` to end the request at the decision |
| `default_bucket` | where a request goes when it is not judged (judgement failed, timed out, no text) or is judged below `min_confidence`. Defaults to the first bucket; required when the first bucket has no models |
| `force_bucket` | skip the judgement and use this bucket; no judgement is charged |
| `min_confidence` | below this `confidence`, use `default_bucket` (`reason: "unsure"`); the judgement is still charged |
| `ladder`, `state` | conversation mode, below |

A single bucket is a fallback chain: no judgement, nothing charged for one. A setting you leave out keeps its default.

Write `when` the way you would explain the bucket to a person, and make the buckets cover every request between them. One bucket with `models: []` plus `default_bucket` set to a bucket with models is the pattern for "stop spam, answer the rest".

## Reading `meta.router`

It is on the response body next to `meta.usage` and `meta.model`. In a Chat Completions stream it is on the last chunk (the OpenAI Python SDK keeps it in `chunk.model_extra["meta"]`); in a routed Messages stream on the `message_stop` event; in other streams on the last event.

| Field | Meaning |
| ----- | ------- |
| `id` | the router you called |
| `routed` | `false`: the bucket had no models, nothing answered, the answer is empty in the endpoint's shape (`content: ""`, `data: []`, a video with `video: null`). Act on `bucket` |
| `bucket` | where the request landed |
| `spilled_from` | the bucket it was judged into when none of that bucket's models could take it (tools, images, JSON schema, size) |
| `reason` | `classified`, `forced`, `single_bucket`, `sticky`, `unsure`, `no_text`, `no_eligible_candidate`, `fallback_only`, or a failed judgement: `classifier_timeout`, `classifier_error`, `classifier_unreadable`, `classifier_refused`, `classifier_circuit_open` |
| `decision_model`, `choice`, `confidence` | who judged, what it picked, how sure it was |
| `judgement` | `inference_id`, `credits`, `images` shown, `images_unseen` |
| `judgements[]` | ladder turns judged in several pieces |
| `state` | ladder state to send back |

`meta.model` is the model that answered. A failed judgement never fails the request; it shows up only as a `classifier_*` reason. Count those reasons in your logs, and choose `default_bucket` as the bucket that is safe to land in when the router could not judge.

```python
meta = (resp.model_extra or {}).get("meta", {})   # OpenAI SDK, non-streaming
route = meta.get("router", {})
if route.get("routed") is False and route.get("bucket") == "spam":
    reject()
```

## Ladders (conversations)

With `ladder: true` the buckets are rungs, strictest first. Each new turn is judged and the conversation moves down to the lowest rung it needs and stays there; it never moves back up until what moved it is gone from the history. Send each answer's `meta.router.state` back unchanged as `router.state` with the next turn, so only what is new is judged. Without it the whole conversation is judged again in pieces, each piece charged as its own judgement. `force_bucket` is not allowed with a ladder. To fail closed, name the last rung as `default_bucket`. A Responses turn that continues a stored response with `previous_response_id` needs no `state`.

## Cost

| Part | Where you see it |
| ---- | ---------------- |
| The answer, at the answering model's rate | `meta.usage`, the `x-aimlapi-credits-used` and `x-aimlapi-usd-spent` headers |
| The judgement, at the decision model's catalogue price, images as its input tokens | `meta.router.judgement.credits`; its own row in `GET /v2/logs`, with `inference_id` equal to `judgement.inference_id` and the router as `client` |

The total for a request is both. A request that ends at the decision (`routed: false`) pays only the judgement. Forced buckets, single buckets and turns that return tool results pay no judgement. The router entries in the catalogue have `pricing.kind: variable`: there is no price to quote before the call.

## Testing

Sandbox mode answers a router request with a fixed chat message, without `meta.router`, and does not validate the `router` object (a chat model as `decision_model` still gets `200`). Unit-test your `meta.router` handling against a recorded live response, and send one small live request per router setup before relying on it.
