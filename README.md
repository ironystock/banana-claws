# banana-claws

[![CI](https://github.com/ironystock/banana-claws/actions/workflows/ci.yml/badge.svg)](https://github.com/ironystock/banana-claws/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/ironystock/banana-claws?sort=semver)](https://github.com/ironystock/banana-claws/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)
[![Issues](https://img.shields.io/github/issues/ironystock/banana-claws)](https://github.com/ironystock/banana-claws/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)

`banana-claws` is a public OpenClaw skill and script toolkit for OpenRouter image generation, designed for both autonomous agents and human builders. It supports fast single-image generation, queue-first batch workflows, and machine-readable result artifacts so orchestration systems can acknowledge quickly, process in background, and return consolidated attached outputs.

## Fast install (copy/paste for agents)

If you are instructing another OpenClaw agent, use this instruction block verbatim:

```text
Install the OpenClaw skill `banana-claws` from:
https://github.com/ironystock/banana-claws

Steps:
1) Clone repo
2) Copy `skill/` contents into ~/.openclaw/workspace/skills/banana-claws/
3) Ensure OPENROUTER_API_KEY is set in runtime env
4) Restart/reload agent runtime so skills are re-indexed
5) Verify skill discovery, then run a queue-mode smoke test with attached outputs
```

Recommended smoke-test prompt for the agent:

```text
Use banana-claws to generate 2 variants of "neon cyberpunk crab logo" in queue mode.
Acknowledge queued immediately, then return a consolidated completion status and attach outputs.
```

## Best install path for external agents

- **Preferred:** install from GitHub repo source (`skill/` directory), not from release zip.
- **Why:** agents reliably understand repo URL + folder copy instructions; zip handling varies across runtimes/tools.
- **If using release zip anyway:** extract it first, then manually copy `skill/` into the OpenClaw skills directory.

## What this includes

- `skill/SKILL.md` — skill instructions + queue/response pattern
- `skill/scripts/generate_image.py` — single image generation
- `skill/scripts/enqueue_image_job.py` — enqueue one job
- `skill/scripts/enqueue_variants.py` — enqueue N variants with consistent naming
- `skill/scripts/run_image_queue.py` — drain queue and write success/failure job records
- `skill/scripts/queue_and_return.py` — enqueue + immediate return + background worker handoff
- `skill/scripts/summarize_request.py` — summarize request completion/attachments for push reporting
- `skill/scripts/preflight_check.py` — first-run diagnostics + copy/paste fixups

## Requirements

- Python 3.9+
- `OPENROUTER_API_KEY` environment variable
- Internet access to `https://openrouter.ai`

Install Python dependency:

```bash
pip install -r requirements.txt
```

## Quick start

### 0) First-time setup check (FTUX)

```bash
python3 skill/scripts/preflight_check.py
python3 skill/scripts/preflight_check.py --json
```

Generate one image:

```bash
python3 skill/scripts/generate_image.py \
  --prompt "A cinematic portrait of a cyberpunk crab" \
  --model google/gemini-3.1-flash-image-preview \
  --image-size low \
  --clarify-hints \
  --out ./generated/cyber-crab.png
```

Queue 4 variants with async handoff (recommended):

```bash
python3 skill/scripts/queue_and_return.py \
  --prompt "YouTube thumbnail: Snowcrab AI — Queue Mode Test, neon cyberpunk" \
  --count 4 \
  --baseline-image ./generated/base-thumbnail.png \
  --baseline-source-kind explicit_path_or_url \
  --variation-strength low \
  --lock-palette \
  --lock-composition \
  --must-keep "title placement" \
  --must-keep "logo region" \
  --image-size low \
  --clarify-hints \
  --out-dir ./generated \
  --prefix snowcrab-queue-test \
  --request-id "discord-<message-id>" \
  --queue-dir ./generated/imagegen-queue
```

Manual worker drain (worker context only):

```bash
python3 skill/scripts/run_image_queue.py --queue-dir ./generated/imagegen-queue --request-id "discord-<message-id>" --handoff-mode background
```

### Iteration vs final quality

- Use `--image-size low` for fast/low-cost exploratory passes.
- Use `--image-size medium` or `--image-size high` for final-quality outputs.

### Prompt clarity hints

- Add `--clarify-hints` to print actionable prompt-quality hints (style, size/format, exact text, composition constraints).
- Add `--strict-clarify` to fail early when prompt appears underspecified.

### Baseline-locked variants (on-rails)

- Use `--baseline-image` for true image-to-image varianting.
- Resolve baseline deterministically in caller: **current-message attachment > replied-message attachment > clarification request**.
- Record baseline provenance with `--baseline-source-kind current_attachment|reply_attachment|explicit_path_or_url`.
- Edit/variant intent prompts fail fast when no baseline is provided (override only with `--allow-no-baseline-on-edit-intent`).
- Default rails are auto-applied when baseline is present: `variation-strength=low`, `lock-palette`, `lock-composition`.
- Use `--variation-strength low|medium|high` to control divergence from baseline.
- Use repeatable `--must-keep` constraints for consistency.
- `enqueue_variants.py` writes a `<prefix>-manifest.json` file for reproducible reruns/debugging.

## Queue/result contract

- Pending jobs: `generated/imagegen-queue/pending/*.json`
- Success records: `generated/imagegen-queue/results/*.json`
- Failure records: `generated/imagegen-queue/failed/*.json`

Each result/failed record includes `request_id`, `out`, `exit_code`, stdout/stderr, and persisted provider metadata (including top-level generation id and provider response payload/path) for orchestration and edit/debug workflows.

Drift diagnostics are also persisted per job (`edit_intent_detected`, `baseline_applied`, `baseline_source`, `baseline_source_kind`, `baseline_resolution_policy`, `rails_applied`, `clarify_hints`) so agents can prove whether baseline rails were actually used.

Messaging behavior note:
- For multi-image requests, send an immediate queued ack, then a consolidated completion status update.
- **Do not run queue drain in the same foreground turn** for multi-image requests.
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

## Agent -> user recovery prompts (copy/paste)

- Missing API key:
  - `I can generate images once OPENROUTER_API_KEY is set. Please run: export OPENROUTER_API_KEY="<your_key>" then tell me to retry.`
- Missing Python:
  - `I need python3 to run banana-claws scripts. Please install Python 3 and confirm 'python3 --version' works, then I’ll continue.`
- Queue folder missing:
  - `Queue mode needs a queue directory. Please run: mkdir -p ./generated/imagegen-queue and I’ll proceed.`

## Publishing notes

This repo is GitHub-first for now. ClawHub packaging can be added later once account eligibility is available.
