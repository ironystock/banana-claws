# banana-claws

`banana-claws` is a public OpenClaw skill and script toolkit for OpenRouter image generation, designed for both autonomous agents and human builders. It supports fast single-image generation, queue-first batch workflows, and machine-readable result artifacts so orchestration systems can acknowledge quickly, process in background, and return consolidated attached outputs.

## What this includes

- `skill/SKILL.md` — skill instructions + queue/response pattern
- `skill/scripts/generate_image.py` — single image generation
- `skill/scripts/enqueue_image_job.py` — enqueue one job
- `skill/scripts/enqueue_variants.py` — enqueue N variants with consistent naming
- `skill/scripts/run_image_queue.py` — drain queue and write success/failure job records

## Requirements

- Python 3.9+
- `OPENROUTER_API_KEY` environment variable
- Internet access to `https://openrouter.ai`

Install Python dependency:

```bash
pip install -r requirements.txt
```

## Quick start

Generate one image:

```bash
python3 skill/scripts/generate_image.py \
  --prompt "A cinematic portrait of a cyberpunk crab" \
  --model google/gemini-3.1-flash-image-preview \
  --out ./generated/cyber-crab.png
```

Queue 4 variants:

```bash
python3 skill/scripts/enqueue_variants.py \
  --prompt "YouTube thumbnail: Snowcrab AI — Queue Mode Test, neon cyberpunk" \
  --count 4 \
  --out-dir ./generated \
  --prefix snowcrab-queue-test \
  --request-id "discord-<message-id>"
```

Process queue:

```bash
python3 skill/scripts/run_image_queue.py --queue-dir ./generated/imagegen-queue
```

## Queue/result contract

- Pending jobs: `generated/imagegen-queue/pending/*.json`
- Success records: `generated/imagegen-queue/results/*.json`
- Failure records: `generated/imagegen-queue/failed/*.json`

Each result/failed record includes `request_id`, `out`, `exit_code`, and stdout/stderr for orchestration and reporting.

## Publishing notes

This repo is GitHub-first for now. ClawHub packaging can be added later once account eligibility is available.
