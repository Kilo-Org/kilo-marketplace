# Media Guide

Use `media` for standalone image generation. Use App Builder when images are only one part of a live application, and artifacts for durable reports or charts.

## Choose an input mode

- **One image**: pass a prompt directly. Add a local reference image when the result should follow an existing visual.
- **Batch**: supply a JSON image list (or `{ "items": [...] }`) from a file or stdin. Download batches to a directory, not a single output path.
- Let the project default choose the model unless the user requests a specific model available in the project's AI settings. Aspect ratio support depends on that model.

## Task workflow

1. Start generation with `media generate` and retain the returned task ID.
2. For work that is not yet complete, use `media get` rather than submitting the prompt again. Wait when the user needs all results; otherwise inspect completed images incrementally.
3. If the original submission response was interrupted, retry with the same stable request ID to recover it instead of creating duplicate work.
4. Use `media cancel` only after confirmation when the user no longer wants pending images. Cancellation preserves images already completed.

## Output decisions

- For a single image needed locally, write to a new file.
- For a batch, use a directory; later retrieval can download completed results there without regenerating.
- Without a local output target, generated images remain available through the task/ChatFile result.
- Do not overwrite an existing local deliverable implicitly; choose a new path or confirm replacement first.

## Common pitfalls

| Pitfall | Safer action |
|---------|--------------|
| Resubmitting because generation is still running | Poll the task ID with `media get` |
| Retrying an uncertain submission with a new identity | Reuse the original request ID |
| Sending batch JSON to the single-prompt mode | Put the list in an input file or pipe it on stdin |
| Canceling to remove completed results | Do not cancel; cancellation only stops pending work and preserves completed images |
| Guessing model-specific ratios | Use the project default or verify support in the project's AI settings |
