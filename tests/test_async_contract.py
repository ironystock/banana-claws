#!/usr/bin/env python3
import json
import pathlib
import subprocess
import tempfile
import time


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[1]
    script = root / 'skill' / 'scripts' / 'queue_and_return.py'
    queue_dir = pathlib.Path(tempfile.mkdtemp(prefix='banana-claws-queue-'))
    out_dir = pathlib.Path(tempfile.mkdtemp(prefix='banana-claws-out-'))

    request_id = f'test-{int(time.time())}'
    cmd = [
        'python3',
        str(script),
        '--prompt',
        'Generate 2 simple icon variants.',
        '--count',
        '2',
        '--out-dir',
        str(out_dir),
        '--prefix',
        't',
        '--request-id',
        request_id,
        '--queue-dir',
        str(queue_dir),
        '--dry-run-worker',
    ]

    t0 = time.time()
    cp = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0

    if cp.returncode != 0:
        print(cp.stderr or cp.stdout)
        return 1

    data = json.loads(cp.stdout.strip())
    assert data['status'] == 'queued'
    assert data['handoff_mode'] == 'background'
    assert elapsed < 2.0, f'Expected immediate return <2s, got {elapsed:.3f}s'

    handoff = pathlib.Path(data['handoff_file'])
    assert handoff.exists(), 'handoff file missing'
    h = json.loads(handoff.read_text())
    assert h['handoff_mode'] == 'background'

    print('ok')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
