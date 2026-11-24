# Request shapes

Every decision model is on `POST /v1/decisions`, but not every model takes the same body. The model's `info.docsJson` in `GET /v1/models?type=internal/decisions` is the authority; `python3 scripts/decide.py shape <model>` prints the parts that matter. What follows is the structure of the two shapes, not a list of which model takes what: that changes, so read it per model.

## System One shape

Most decision models (TypeSafe Jev, Liquid d1, HeyGen Decision, Gemini Decision at the time of writing) take this shape.

| Field | Type | Notes |
| ----- | ---- | ----- |
| `model` | string | the catalogue id |
| `state` | string, JSON object, or array of texts | the content to judge. Some models make it optional, for questions that stand alone |
| `questions` | object: your key to a question | each key comes back in `answers`. The schema gives the most keys per request |
| `images` | array of image URLs or `data:` URLs | models that read images this way; refer to an image by its position |
| `assets` | object: reference string to `{type, format, data_base64}` | models that read images this way: write the reference where the image belongs in the state or a question |
| `videos`, `audios` | arrays of public `https://` URLs | only models whose schema lists them |

A media field the model does not take is still in its schema, with `maxItems: 0` or a description that starts "Not supported": a non-empty value is refused with a `400`. Image limits (format, pixels per side, patches, request size) are in the field's description; images are never resized.

### Question types

| `type` | Needs | Optional | Asks |
| ------ | ----- | -------- | ---- |
| `noul` | `instructions` | `criteria: {"true": …, "false": …}` | yes or no |
| `choice` | `instructions`, `criteria` (option key to description, or `null` when the key says it all) | `multiple: true` on models that list it | one option, or every option that applies |
| `score` | `instructions`, `criteria` (array of levels, lowest first) | | a place on an ordered scale |
| `text`, `number`, `date` | `instructions` | `number`: `unit`, `range`, `step` | read one value from the state, or estimate a number within `range` |
| `spans` | `instructions` | `max` | every passage of a kind, such as each piece of personal data |
| `box`, `boxes` | `instructions` | `boxes`: `max` | where one object, or every instance, is in an image |

Only `noul`, `choice` and `score` are on every System One model. The others are on the models whose schema lists them, and the minimum number of `choice` options differs (one model accepts 1, others need 2). `instructions` and every description may be text or a JSON object or array.

Some models bill every slot of `spans` and `boxes` whether it is filled or not, and some show every image to every question again: the field descriptions say so, and it multiplies the cost.

### Example with images

```json
{
  "model": "liquid/d1.2",
  "state": "Photo from a delivery driver.",
  "images": ["data:image/jpeg;base64,/9j/4AAQ..."],
  "questions": {
    "damaged": {"type": "noul", "instructions": "Is the parcel in the image damaged?"},
    "where": {"type": "box", "instructions": "The parcel"}
  }
}
```

A model that takes `assets` instead names the image by a reference you choose:

```json
{
  "model": "typesafe/jev",
  "state": {"photo": "a3f1c2e8-door"},
  "assets": {"a3f1c2e8-door": {"type": "image", "format": "jpg", "data_base64": "/9j/4AAQ..."}},
  "questions": {"open": {"type": "noul", "instructions": "Is the door in `photo` open?"}}
}
```

Every asset must be referenced. A request whose `assets` reach a fallback provider that cannot take them is refused with a `400` that asks you to retry shortly.

## OpenAI Decisions shape

A model in OpenAI's Decisions format (`openai/gpt-6-luna` at the time of writing) takes:

| Field | Type | Notes |
| ----- | ---- | ----- |
| `input` | string, or an array of `message` items with roles `user`, `system`, `developer`, `assistant` | user messages may mix `input_text` and `input_image` parts |
| `questions` | array of items, each with a unique `name` | answers come back in the same order |
| `prompt_cache_key` | string | optional |

| `type` | Needs |
| ------ | ----- |
| `predicate` | `name`, `instructions` |
| `choice` | `name`, `instructions`, `choices: [{value, description?}]` |
| `score` | `name`, `instructions`, `levels: [{label, description?}]`, lowest first |

```json
{
  "model": "openai/gpt-6-luna",
  "input": "I was charged twice for my order.",
  "questions": [
    {"type": "predicate", "name": "refund", "instructions": "Is the customer asking for money back?"},
    {"type": "choice", "name": "team", "instructions": "Which team handles this?",
     "choices": [{"value": "billing", "description": "Payments and refunds"}, {"value": "other"}]},
    {"type": "score", "name": "severity", "instructions": "How bad is it?",
     "levels": [{"label": "Minor"}, {"label": "Blocking"}]}
  ]
}
```

## Moving a question between shapes

| System One | OpenAI Decisions |
| ---------- | ---------------- |
| `state` | `input` |
| `questions: {"key": {...}}` | `questions: [{"name": "key", ...}]` |
| `noul` | `predicate` |
| `choice.criteria: {"billing": "Payments"}` | `choice.choices: [{"value": "billing", "description": "Payments"}]` |
| `score.criteria: ["Calm", "Angry"]` | `score.levels: [{"label": "Calm"}, {"label": "Angry"}]` |

Sending `state` with an object of questions to an OpenAI-shape model returns `400` with `error.details` naming `input` and `questions` ("Expected array, received object"); the reverse fails the same way.
