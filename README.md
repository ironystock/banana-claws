# banana-claws

[![CI](https://github.com/ironystock/banana-claws/actions/workflows/ci.yml/badge.svg)](https://github.com/ironystock/banana-claws/actions/workflows/ci.yml)

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
  --image-size low \
  --clarify-hints \
  --out ./generated/cyber-crab.png
```

Queue 4 variants:

```bash
python3 skill/scripts/enqueue_variants.py \
  --prompt "YouTube thumbnail: Snowcrab AI — Queue Mode Test, neon cyberpunk" \
  --count 4 \
  --image-size low \
  --clarify-hints \
  --out-dir ./generated \
  --prefix snowcrab-queue-test \
  --request-id "discord-<message-id>"
```

Process queue:

```bash
python3 skill/scripts/run_image_queue.py --queue-dir ./generated/imagegen-queue
```

### Iteration vs final quality

- Use `--image-size low` for fast/low-cost exploratory passes.
- Use `--image-size medium` or `--image-size high` for final-quality outputs.

### Prompt clarity hints

- Add `--clarify-hints` to print actionable prompt-quality hints (style, size/format, exact text, composition constraints).
- Add `--strict-clarify` to fail early when prompt appears underspecified.

## Queue/result contract

- Pending jobs: `generated/imagegen-queue/pending/*.json`
- Success records: `generated/imagegen-queue/results/*.json`
- Failure records: `generated/imagegen-queue/failed/*.json`

Each result/failed record includes `request_id`, `out`, `exit_code`, and stdout/stderr for orchestration and reporting.

Messaging behavior note:
- For multi-image requests, send an immediate queued ack, then a consolidated completion status update.
- Always attach generated files (never path-only).
- If your message adapter only supports one attachment per send, post file attachments as replies under the completion status message.

## Install & use in OpenClaw (GitHub)

### 1) Clone the repo

```bash
git clone https://github.com/ironystock/banana-claws.git
cd banana-claws
```

### 2) Place the skill where OpenClaw can discover it

Copy the `skill/` folder into your OpenClaw skills workspace (example shown below):

```bash
mkdir -p ~/.openclaw/workspace/skills/banana-claws
cp -R skill/* ~/.openclaw/workspace/skills/banana-claws/
```

### 3) Set required environment variable

```bash
export OPENROUTER_API_KEY="your_openrouter_api_key"
```

### 4) Refresh/restart agent runtime so skills are re-indexed

If the running agent session does not see the skill yet, restart/reload your OpenClaw runtime/session and verify the new skill is discoverable.

### 5) Prompt examples that should trigger this skill

- "Generate a cyberpunk poster concept image with neon blue lighting."
- "Create 4 thumbnail variants in queue mode and attach results when done."
- "Make a mascot concept art set and return a consolidated completion with all files."

### 6) What users should provide in prompts

For best results, include:

- subject (what image to generate)
- style/aesthetic (e.g., cinematic, pixel art, flat vector)
- text requirements (exact words if text must appear)
- output intent (single image vs batched variants)
- constraints (format, dimensions, size cap)

## Project docs

- Contribution guide: [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- Release notes: [`CHANGELOG.md`](./CHANGELOG.md)

## Publishing notes

This repo is GitHub-first for now. ClawHub packaging can be added later once account eligibility is available.
