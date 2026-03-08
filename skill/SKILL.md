---
name: banana-claws
description: Generate images via OpenRouter API (text-to-image) with automation-ready local scripts and a queue-first workflow. Use for single images or batched variants (posters, thumbnails, illustrations, concept art), especially when agents must acknowledge quickly, process asynchronously, and return consolidated file attachments with structured success/failure records.
---

# OpenRouter Image Generation

Generate images from prompts using OpenRouter's image generation endpoint.

## Requirements

- `OPENROUTER_API_KEY` in environment
- `python3`

## Default model

- `google/gemini-3.1-flash-image-preview`
- Optional alternatives (if enabled on your account): `openai/gpt-5-image`, `openai/gpt-5-image-mini`

## Usage

```bash
python3 {baseDir}/scripts/generate_image.py \
  --prompt "A cinematic portrait of a cyberpunk crab" \
  --model google/gemini-3.1-flash-image-preview \
  --out ./generated/cyber-crab.png
```

Optional args:

```bash
--model openai/gpt-5-image
--model openai/gpt-5-image-mini
```

## Queue -> response pattern (avoid traffic jams)

When a user asks for multiple images/iterations, do **not** hold one long-running turn per image.
Use a queue + batched response flow:

1. Enqueue each requested image quickly.
2. **Immediately return** with a short "queued" acknowledgement (do not wait for generation in the same turn).
3. Drain queue in background (preferred: sub-agent/session worker).
4. Send one consolidated completion response when done.
5. **Always attach generated image files in the completion response.** Never send only paths.

Enqueue command:

```bash
python3 {baseDir}/scripts/enqueue_image_job.py \
  --prompt "A retro 80s crab poster" \
  --model google/gemini-3.1-flash-image-preview \
  --out ./generated/crab-01.png \
  --request-id "discord-<message-id>"
```

Drain queue command:

```bash
python3 {baseDir}/scripts/run_image_queue.py \
  --queue-dir ./generated/imagegen-queue
```

Batch-enqueue N variants with consistent file names:

```bash
python3 {baseDir}/scripts/enqueue_variants.py \
  --prompt "A minimalist snow crab logo" \
  --count 4 \
  --out-dir ./generated \
  --prefix crab-logo \
  --request-id "discord-<message-id>"
```

Useful options:

```bash
--max-jobs 3   # process only a subset for controlled batches
--start-index 5  # continue naming from prior batches
```

## Notes

- If generation fails due to model/provider mismatch, retry with `--model openai/gpt-5-image-mini`.
- Keep prompts explicit for text rendering tasks.
- Save outputs into workspace paths, not `/tmp`, for durability.
- When user asks for generated images in chat, attach the generated file in the response (do not only send a path).
- For queue mode, read results from:
  - `.../imagegen-queue/results/*.json` (success)
  - `.../imagegen-queue/failed/*.json` (failure details)
