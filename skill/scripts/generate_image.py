#!/usr/bin/env python3
import argparse
import base64
import json
import os
import pathlib
import re
import sys
from typing import List

import requests


def _needs_clarification(prompt: str) -> list[str]:
    text = prompt.lower()
    hints: list[str] = []

    if not re.search(r"\b(\d{3,4}x\d{3,4}|thumbnail|banner|poster|icon|avatar|wallpaper|og|social)\b", text):
        hints.append("Output format/size is unclear. Add target like 'thumbnail 1280x720' or 'OG 1280x640'.")

    if not re.search(r"\b(cinematic|pixel|8-bit|vector|realistic|anime|watercolor|cyberpunk|minimal|gritty|retro|flat)\b", text):
        hints.append("Style is unclear. Add style keywords (e.g., cinematic, pixel-art, flat vector).")

    if re.search(r"\b(text|title|headline|logo|wordmark)\b", text) and not re.search(r"['\"“”][^'\"“”]{2,}['\"“”]", prompt):
        hints.append("Text rendering requested but exact copy is missing. Put required text in quotes.")

    if not re.search(r"\b(high contrast|readable|legible|safe area|centered|negative space)\b", text):
        hints.append("Composition constraints are vague. Consider adding readability/composition constraints.")

    return hints


def _read_baseline_as_data_url(path_or_url: str) -> str:
    if path_or_url.startswith('http://') or path_or_url.startswith('https://'):
        return path_or_url

    p = pathlib.Path(path_or_url)
    if not p.exists():
        raise FileNotFoundError(f'Baseline image not found: {path_or_url}')

    mime = 'image/png'
    suffix = p.suffix.lower()
    if suffix in ('.jpg', '.jpeg'):
        mime = 'image/jpeg'
    elif suffix == '.webp':
        mime = 'image/webp'

    b = p.read_bytes()
    return f'data:{mime};base64,' + base64.b64encode(b).decode('ascii')


def _build_variant_constraint_text(args: argparse.Namespace) -> str:
    lines: List[str] = []
    if args.baseline_image:
        lines.append('Use the provided baseline image as the primary composition anchor.')
    if args.variation_strength:
        lines.append(f'Variation strength: {args.variation_strength}.')
    if args.lock_palette:
        lines.append('Lock color palette close to baseline.')
    if args.lock_composition:
        lines.append('Lock composition/layout close to baseline.')
    if args.must_keep:
        lines.append('Must-keep elements: ' + '; '.join(args.must_keep))
    return '\n'.join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--prompt', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--model', default='openai/gpt-5-image')
    p.add_argument('--image-size', choices=['low', 'medium', 'high'], default='', help='Model-dependent quality/size tier for iterative vs final passes')
    p.add_argument('--clarify-hints', action='store_true', help='Print prompt-clarification hints before generation')
    p.add_argument('--strict-clarify', action='store_true', help='Fail fast if prompt appears ambiguous for production-style tasks')
    p.add_argument('--baseline-image', default='', help='Path/URL to baseline image for locked variants')
    p.add_argument('--variation-strength', choices=['low', 'medium', 'high'], default='')
    p.add_argument('--must-keep', action='append', default=[], help='Repeatable constraint for required elements')
    p.add_argument('--lock-palette', action='store_true')
    p.add_argument('--lock-composition', action='store_true')
    args = p.parse_args()

    key = os.getenv('OPENROUTER_API_KEY')
    if not key:
        print('OPENROUTER_API_KEY is not set', file=sys.stderr)
        return 2

    clarify = _needs_clarification(args.prompt)
    if args.clarify_hints and clarify:
        for h in clarify:
            print(f'CLARIFY_HINT: {h}', file=sys.stderr)

    if args.strict_clarify and clarify:
        print('Prompt requires clarification before generation:', file=sys.stderr)
        for h in clarify:
            print(f'- {h}', file=sys.stderr)
        return 3

    url = 'https://openrouter.ai/api/v1/chat/completions'

    extra_constraints = _build_variant_constraint_text(args)
    final_prompt = args.prompt if not extra_constraints else f"{args.prompt}\n\n{extra_constraints}"

    if args.baseline_image:
        try:
            img_url = _read_baseline_as_data_url(args.baseline_image)
        except Exception as e:
            print(str(e), file=sys.stderr)
            return 2
        content = [
            {'type': 'text', 'text': final_prompt},
            {'type': 'image_url', 'image_url': {'url': img_url}},
        ]
    else:
        content = final_prompt

    payload = {
        'model': args.model,
        'messages': [
            {'role': 'user', 'content': content}
        ],
        'modalities': ['image', 'text'],
    }
    if args.image_size:
        payload['image_size'] = args.image_size

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
