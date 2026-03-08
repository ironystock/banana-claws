#!/usr/bin/env python3
import argparse
import base64
import json
import os
import pathlib
import sys
import requests


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--prompt', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--model', default='openai/gpt-5-image')
    args = p.parse_args()

    key = os.getenv('OPENROUTER_API_KEY')
    if not key:
        print('OPENROUTER_API_KEY is not set', file=sys.stderr)
        return 2

    url = 'https://openrouter.ai/api/v1/chat/completions'
    # OpenRouter image generation uses chat completions + modalities
    # (per docs: /guides/overview/multimodal/image-generation)
    payload = {
        'model': args.model,
        'messages': [
            {'role': 'user', 'content': args.prompt}
        ],
        'modalities': ['image', 'text'],
    }
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    }

    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=180)
    if r.status_code >= 300:
        print(f'Generation failed: {r.status_code} {r.text[:500]}', file=sys.stderr)
        return 1

    data = r.json()
    choices = data.get('choices') or []
    if not choices:
        print('No choices returned', file=sys.stderr)
        return 1

    msg = (choices[0] or {}).get('message') or {}
    images = msg.get('images') or msg.get('image') or []
    if isinstance(images, dict):
        images = [images]
    if not images:
        print(f'No images found in response message: keys={list(msg.keys())}', file=sys.stderr)
        return 1

    first = images[0]
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # common shapes:
    # {"image_url": {"url": "data:image/png;base64,..."}}
    # {"imageUrl": {"url": "..."}}
    # {"url": "https://..."}
    data_url = None
    if isinstance(first, dict):
        if isinstance(first.get('image_url'), dict):
            data_url = first['image_url'].get('url')
        if not data_url and isinstance(first.get('imageUrl'), dict):
            data_url = first['imageUrl'].get('url')
        if not data_url:
            data_url = first.get('url')

    if not data_url:
        print('Unsupported image payload shape', file=sys.stderr)
        return 1

    if data_url.startswith('data:image') and 'base64,' in data_url:
        b64 = data_url.split('base64,', 1)[1]
        out.write_bytes(base64.b64decode(b64))
    elif data_url.startswith('http://') or data_url.startswith('https://'):
        img = requests.get(data_url, timeout=180)
        img.raise_for_status()
        out.write_bytes(img.content)
    else:
        print('Unknown image URL format', file=sys.stderr)
        return 1

    print(str(out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
