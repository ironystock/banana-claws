# Contributing to banana-claws

Thanks for contributing.

## Quick setup

1. Fork + clone the repo.
2. Install dependency:
   ```bash
   pip install -r requirements.txt
   ```
3. Run script smoke checks:
   ```bash
   python3 skill/scripts/generate_image.py --help
   python3 skill/scripts/enqueue_image_job.py --help
   python3 skill/scripts/enqueue_variants.py --help
   python3 skill/scripts/run_image_queue.py --help
   ```

## Branch and PR flow

- Create a feature branch from `main`.
- Keep changes focused and documented.
- Open a PR with clear before/after behavior.
- Link related issue(s) when applicable.

## Contribution priorities

- Reliability of queue/result workflow
- Better error handling and diagnostics
- Docs and examples for builder onboarding
- CI and testing improvements

## Notes

- Do not commit API keys or secrets.
- Prefer deterministic output/contract changes.
- For behavior changes, update `README.md` and/or `skill/SKILL.md` in the same PR.
