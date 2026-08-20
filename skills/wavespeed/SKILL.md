---
name: wavespeed
description: >-
  Generate or edit AI media (image, video, audio, 3D) by calling the wavespeed
  CLI on the user's machine. Use whenever the user asks to create, edit,
  animate, upscale, or transform a visual asset, generate audio/TTS/music, or
  produce marketing creatives. Every model on the WaveSpeed platform is one
  `wavespeed run <id>` call.
metadata:
  category: creative-media
  author: WaveSpeedAI
  source:
    repository: 'https://github.com/WaveSpeedAI/claude-plugins'
    path: plugins/wavespeed/skills/wavespeed
    license_path: LICENSE
    ref: main
    commit: 2807ab7cec7e3a89dfe85ed6bb6444d859627ac2
---

# WaveSpeed

You have access to the `wavespeed` CLI. Every generation flows through one verb. There are no `image` / `video` shortcuts; the model id is always explicit.

## The three-step pattern

```bash
# 1. FIND a model — search the live catalog
wavespeed models "seedream"
wavespeed models --type image-to-video --popular

# 2. INSPECT its inputs — dynamic schema, per model
wavespeed run bytedance/seedream-v5.0-pro -h

# 3. RUN it — always pass --json so you can read the result
wavespeed run bytedance/seedream-v5.0-pro \
  -p "a cyberpunk skyline at golden hour" \
  -i aspect_ratio="16:9" -i resolution="2k" --json
```

`run --json` returns `{ id, model, prompt, outputs: [url, ...], saved: [path, ...], elapsed_ms, raw }`. Keep `id` — it is the handle for `wavespeed show <id>` if anything is interrupted. Use the URL when the user wants a link. Add `--download` if they need bytes on disk.

## Recommended defaults

| Use case | Model |
|---|---|
| Text → image | `bytedance/seedream-v5.0-pro` |
| Image edit (instruction-driven) | `bytedance/seedream-v5.0-pro/edit` — requires `images: [url, ...]` |
| Text → video | `bytedance/seedance-2.5/text-to-video` |
| Image → video | `bytedance/seedance-2.5/image-to-video` — requires `image: url` |
| Video edit (instruction-driven) | `bytedance/seedance-2.5/video-edit` — requires `video: url` |
| Video extend | `bytedance/seedance-2.5/video-extend` — requires `video: url` |

These are good starting points. Browse alternatives with `wavespeed models <query>`.

## Common recipes

```bash
# Edit an existing image — @path uploads the file and passes its URL (one step)
wavespeed run bytedance/seedream-v5.0-pro/edit \
  -p "replace the background with a sunlit kitchen" \
  -i images='["@./input.jpg"]' --json

# Image-to-video — same @ marker for single-URL fields
wavespeed run bytedance/seedance-2.5/image-to-video \
  -p "subtle parallax, gentle wind" \
  -i image=@./hero.jpg -i duration=5 --json

# Or upload separately when you need the URL itself
URL=$(wavespeed upload ./hero.jpg --json | jq -r .url)

# Save outputs locally with a template
wavespeed run ... -p "..." --download "./out/{index}.{ext}"
```

## Project config and aliases

If `wavespeed.json` exists (created by `wavespeed init`):

- **`defaultModel`** — lets `wavespeed run -p "…"` (no model arg) work.
- **Aliases** — named shortcuts that bundle model + default inputs. Run `wavespeed aliases` to see what's defined. `wavespeed run <alias> -h` shows the resolved schema. CLI `-i k=v` overrides alias defaults.

The CLI never modifies the user's prompt or inputs. The single exception is explicit: an `@path` value uploads that file and substitutes its hosted URL. Bare paths are never uploaded.

## Auth

`wavespeed status` shows whether the user is signed in. If not, ask them to run `wavespeed login` (opens https://wavespeed.ai/accesskey). **Never** ask the user to paste an API key into the chat — the CLI handles it.

## Pitfalls

- Local files: use `@./file.jpg` in `-i` values. Bare paths are NOT uploaded and the model will reject them.
- Don't invent model IDs. Always confirm via `wavespeed models` or `wavespeed schema <id>` before running.
- Use `--json` on every `run` so you can read `outputs[0]` programmatically.
- `wavespeed delete` requires `--yes` when run non-interactively (that includes you).
- Spend questions: `wavespeed usage` (totals, per-model) and `wavespeed billings` (per-charge records).
