#!/usr/bin/env python3
import argparse
import json
import pathlib
import subprocess
import sys
import time


def _now_ms() -> int:
    return int(time.time() * 1000)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--queue-dir', default='generated/imagegen-queue')
    p.add_argument('--base-dir', default=str(pathlib.Path(__file__).resolve().parents[1]))
    p.add_argument('--max-jobs', type=int, default=0, help='0 means no limit')
    args = p.parse_args()

    queue_dir = pathlib.Path(args.queue_dir)
    pending = queue_dir / 'pending'
    processing = queue_dir / 'processing'
    results = queue_dir / 'results'
    failed = queue_dir / 'failed'
    for d in (pending, processing, results, failed):
        d.mkdir(parents=True, exist_ok=True)

    gen_script = pathlib.Path(args.base_dir) / 'scripts' / 'generate_image.py'
    if not gen_script.exists():
        print(f'Missing generator script: {gen_script}', file=sys.stderr)
        return 2

    processed = 0
    pending_jobs = sorted(pending.glob('*.json'))

    for job_file in pending_jobs:
        if args.max_jobs and processed >= args.max_jobs:
            break

        proc_file = processing / job_file.name
        try:
            job_file.rename(proc_file)
        except FileNotFoundError:
            continue

        job = json.loads(proc_file.read_text())
        job['status'] = 'processing'
        job['started_at_ms'] = _now_ms()
        proc_file.write_text(json.dumps(job, ensure_ascii=False, indent=2) + '\n')

        cmd = [
            sys.executable,
            str(gen_script),
            '--prompt',
            job['prompt'],
            '--out',
            job['out'],
            '--model',
            job.get('model') or 'google/gemini-3.1-flash-image-preview',
        ]

        cp = subprocess.run(cmd, capture_output=True, text=True)
        job['finished_at_ms'] = _now_ms()
        job['exit_code'] = cp.returncode
        job['stdout'] = (cp.stdout or '').strip()
        job['stderr'] = (cp.stderr or '').strip()

        if cp.returncode == 0:
            job['status'] = 'succeeded'
            dest = results / proc_file.name
        else:
            job['status'] = 'failed'
            dest = failed / proc_file.name

        dest.write_text(json.dumps(job, ensure_ascii=False, indent=2) + '\n')
        proc_file.unlink(missing_ok=True)

        processed += 1

    print(json.dumps({'processed': processed, 'queue_dir': str(queue_dir)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
