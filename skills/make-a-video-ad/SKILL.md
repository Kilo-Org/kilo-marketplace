---
name: make-a-video-ad
description: >-
  Plan and make a short video ad or promo clip with the Tesseract connector,
  from a product photo, a logo or a few words. Use when the person asks for a
  video ad, a promo, a product clip, a reel or a multi-scene video and Tesseract
  is connected.
metadata:
  upstream:
    when_to_use: >-
      For example: make a 15-second ad for our bakery from this photo; a promo
      reel for our new sneaker in three scenes; turn this product shot into a
      clip for Instagram Stories.
  category: creative-media
  source:
    repository: 'https://github.com/opentech-dev/tesseract-claude-plugin'
    path: skills/make-a-video-ad
    license_path: LICENSE
    ref: v1.0.0
    commit: e7a5417d1b6e61be609f375937f5ef70f9532eaa
---

# Make a video ad with Tesseract

Tesseract makes the clips; your job is to turn the person's idea into a shot plan, agree the cost, start the job and
bring back the finished file. Every job is charged to the person's own Tesseract plan, so the cost is agreed before
anything starts.

## 1. Understand the ad

Ask only what you need and cannot guess (one short question at most, then go):

- **What is being sold** and the one thing the viewer should remember (the name, the offer, the feeling).
- **Where it will play**, which sets the shape: Reels, Stories, TikTok and Shorts are `9:16`; YouTube and websites
  are `16:9`; a feed post is `1:1`.
- **How long.** 6 to 8 seconds for a single clip; 15 to 30 seconds for a story in scenes.
- **A starting picture.** A product photo or logo makes the ad look like *their* product. It must be a public
  `https://` link or a `data:image/...;base64,...` URI, up to 10 MB.

## 2. Write the shot plan

Write each scene the way a director briefs a camera crew: the subject, the action, the camera move, the light, the
mood. Concrete beats generic: "slow push-in on a sourdough loaf, steam rising, warm morning window light" beats "nice
bread shot".

- **One clip:** one strong idea with a camera move, 4 to 8 seconds.
- **Several scenes:** 2 to 4 scenes for a 15 to 30 second ad. Open on the hook, show the product in use, end on the
  name or the offer. The connector takes up to 12 scenes.
- Put the brand name or the offer in the last scene's prompt if it should appear on screen.

Show the plan to the person in a few lines and let them change it before you spend anything.

## 3. Agree the cost first

1. Call `list_models` with `kind: "video"` to see the video models and which one is the default. Use the default
   unless the person asked for something else.
2. Tell the person the job is charged to their Tesseract plan, and agree a ceiling in US dollars.
3. Pass that ceiling as `max_usd` on the job. A job that would cost more is not started, so the person is never
   charged more than they agreed. If a job is refused for its cost, say so and ask before raising `max_usd`.

## 4. Start the job

- **One clip:** `generate_video` with `prompt`, `aspect_ratio`, `duration_sec`, `max_usd`, and `first_frame` when
  there is a starting picture.
- **Several scenes:** `make_long_video` with `scenes` (each with its own `prompt` and `duration_sec`),
  `aspect_ratio`, `max_usd`, and `first_frame` for the opening picture.
  - `mode: "continuous"` (the default): each scene continues the shot before it, which reads as one film. The first
    scene is 4 to 8 seconds, the others 3 to 10.
  - `mode: "clips"`: every scene is its own clip, all made at once, on any video model. Use it for cuts between
    unrelated shots, or to give each scene its own `first_frame`.

The reply gives a `job_id` and the most the job can cost. Tell the person both.

## 5. Check the job until it is done

- Call `check_job` with the `job_id` every 10 to 20 seconds. A clip takes 1 to 4 minutes; a long video longer.
- In `continuous` mode the next scene is made only when `check_job` finds the one before it finished. Keep checking
  until the job is done; if you stop, nothing more is made or charged.
- Between checks, tell the person briefly what is happening ("scene 2 of 3 is being made").
- When it is done, give the download link. Links last one hour; calling `check_job` again gives fresh ones.

## 6. Offer the next step

Offer one useful follow-up: the other shape for another platform (a `9:16` version of a `16:9` ad), a shorter cut, or
a still picture for the post with `generate_image`. Never start another paid job without the person's yes.

## When not to use this

- The person wants a script, a storyboard or advice only, with no video made: write it yourself.
- The request is for a real person's likeness without their consent, or anything the person may not have the rights
  to use. Say so and ask for material they own.
