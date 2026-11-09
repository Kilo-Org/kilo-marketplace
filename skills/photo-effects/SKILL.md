---
name: photo-effects
description: >-
  Apply one of Tesseract's ready-made effects (camera moves, transformations,
  portraits, seasonal looks, product shots) to the person's own photo or video,
  or make and edit pictures, with the Tesseract connector. Use when the person
  asks to animate a photo, put an effect on a picture or clip, or make or change
  a picture, and Tesseract is connected.
metadata:
  upstream:
    when_to_use: >-
      For example: make this selfie crumble into dust; do a bullet-time spin on
      this photo; animate this picture of my dog; edit this product shot to show
      it in green.
  category: creative-media
  source:
    repository: 'https://github.com/opentech-dev/tesseract-claude-plugin'
    path: skills/photo-effects
    license_path: LICENSE
    ref: v1.0.0
    commit: e7a5417d1b6e61be609f375937f5ef70f9532eaa
---

# Photo effects and pictures with Tesseract

Tesseract has a catalogue of 250+ ready-made effects, plus picture making and editing. Each job is charged to the
person's own Tesseract plan, so check the price before starting one.

## 1. Find the right effect

1. Call `list_effects` once and keep the answer for the rest of the conversation. Each effect has:
   - `id`, `label`, `category` and `description`: what it does;
   - `inputs`: how many pictures it needs, and whether it needs a video or words;
   - `styles`: the looks it offers, if any;
   - `output`: a picture or a clip, and `seconds` for a clip;
   - `price_usd` (and `longer_video` for effects priced by the video's length): the price guide.
2. Match the person's words to the effect's description, not only its name. If two or three fit, show them with
   their price and let the person choose.
3. If the person's photo does not fit what the effect needs (a duo effect needs two pictures, in order: the person
   first, then the other one), say what is missing.

## 2. Agree the cost

Tell the person the price guide from `list_effects` and that it is charged to their Tesseract plan. Pass a ceiling
as `max_usd` on the job: a job that would cost more is not started. If one is refused for its cost, say so and ask
before raising it.

## 3. Apply it

Call `apply_effect` with:

- `effect_id` from `list_effects`;
- `images`: the pictures it needs, in order. Each is a public `https://` link or a `data:image/...;base64,...` URI,
  up to 10 MB;
- `video`: a public `https://` link, for an effect that needs one;
- `prompt` for an effect that takes words, `style` for one of its looks, and `aspect_ratio` and `seconds` for a
  transition;
- `max_usd`.

The reply gives a `job_id` and the most the job can cost. Then call `check_job` every 10 to 20 seconds until it is
done (a clip takes 1 to 4 minutes), and give the person the download link. Links last one hour; calling `check_job`
again gives fresh ones.

## Making and editing pictures

- **A new picture:** `generate_image` with a descriptive `prompt` (subject, setting, light, style, framing),
  `aspect_ratio` and `count` (1 to 8). It usually answers within 40 seconds with download links; if it takes longer
  it returns a `job_id` for `check_job`.
- **Changing a picture:** `edit_image` with the picture, `instructions` written as a short, specific command
  ("make the mug green, keep the marble and the light"), and `reference_images` for anything that should appear or be
  matched.
- `list_models` with `kind: "image"` or `kind: "edit"` shows the other models and the default. Use the default unless
  the person asks.

## Good habits

- One job at a time unless the person asks for variations; never start a paid job the person has not agreed to.
- Say plainly what was made and what it cost (the price is in the job's reply).
- Only use photos of people with their consent, and pictures the person has the right to use. Decline requests to
  deceive or to sexualise anyone.
