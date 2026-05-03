from __future__ import annotations

import re
import uuid
from typing import List, Optional

from symbiotic_swe.contracts import (
    CanonicalTask,
    CritiqueContract,
    PatchContract,
    RetrievedContext,
)
from symbiotic_swe.context_selection.selector import load_context_source
from symbiotic_swe.patch_generation.prompt_builder import SYSTEM_PROMPT, build_patch_prompt

from pathlib import Path


MODEL = 'claude-sonnet-4-6'
MAX_TOKENS = 4096


def _fix_hunk_counts(diff: str) -> str:
    """Recompute @@ -X,Y +X,Y @@ counts from actual hunk content and ensure trailing newline."""
    lines = diff.splitlines()
    result: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^(@@ -)(\d+)(?:,\d+)?( \+)(\d+)(?:,\d+)?( @@.*)', line)
        if m:
            old_start, new_start = int(m.group(2)), int(m.group(4))
            i += 1
            hunk: List[str] = []
            while i < len(lines):
                hl = lines[i]
                if hl.startswith('@@ ') or hl.startswith('diff '):
                    break
                if hl.startswith('--- ') and i + 1 < len(lines) and lines[i + 1].startswith('+++ '):
                    break
                hunk.append(hl)
                i += 1
            old_count = sum(1 for l in hunk if l.startswith(' ') or l.startswith('-'))
            new_count = sum(1 for l in hunk if l.startswith(' ') or l.startswith('+'))
            result.append(f'@@ -{old_start},{old_count} +{new_start},{new_count} {m.group(5).lstrip()}')
            result.extend(hunk)
        else:
            result.append(line)
            i += 1
    return '\n'.join(result) + '\n'


def _extract_diff(raw_text: str) -> str:
    # Collect all ```diff blocks; use the last non-empty one (Claude refines toward the end)
    candidates = re.findall(r'```diff\s*\n(.*?)```', raw_text, re.DOTALL)
    candidates = [c.strip() for c in candidates if c.strip()]
    if candidates:
        return _fix_hunk_counts(candidates[-1])
    # Fallback: unnamed code block that looks like a diff
    blocks = re.findall(r'```\s*\n(.*?)```', raw_text, re.DOTALL)
    for block in reversed(blocks):
        block = block.strip()
        if block.startswith(('diff --git', '--- ', '@@ ', '+')):
            return _fix_hunk_counts(block)
    return ''


def _changed_files(diff: str) -> List[str]:
    files = []
    for line in diff.splitlines():
        if line.startswith('diff --git '):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[2].removeprefix('a/'))
        elif line.startswith('--- a/'):
            files.append(line.removeprefix('--- a/'))
    return list(dict.fromkeys(files))


def generate_patch(
    task: CanonicalTask,
    context: RetrievedContext,
    iteration: int,
    critique: Optional[CritiqueContract] = None,
    repo_path: Optional[Path] = None,
    api_key: Optional[str] = None,
    model: str = MODEL,
) -> PatchContract:
    patch_id = str(uuid.uuid4())[:8]
    context_source = load_context_source(task, context, repo_path)

    messages = build_patch_prompt(task, context_source, iteration, critique)

    import sys
    import time as _time
    import anthropic as _anthropic

    raw_text = ''
    prompt_tokens = 0
    completion_tokens = 0
    last_exc: Optional[Exception] = None

    for attempt in range(3):
        try:
            client = _anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
            raw_text = response.content[0].text
            prompt_tokens = response.usage.input_tokens
            completion_tokens = response.usage.output_tokens
            last_exc = None
            break
        except (_anthropic.APIConnectionError, _anthropic.APITimeoutError) as exc:
            last_exc = exc
            wait = 2 ** attempt
            print(f'  [generator retry {attempt + 1}/3 in {wait}s] {exc}', file=sys.stderr)
            _time.sleep(wait)
        except Exception as exc:
            last_exc = exc
            print(f'  [generator error] {exc}', file=sys.stderr)
            break

    if last_exc is not None:
        return PatchContract(
            patch_id=patch_id,
            task_id=task.task_id,
            iteration=iteration,
            raw_text='',
            diff='',
            errors=[str(last_exc)],
            model=model,
        )

    diff = _extract_diff(raw_text)
    parse_ok = bool(diff.strip())
    target_files = _changed_files(diff) if parse_ok else []

    return PatchContract(
        patch_id=patch_id,
        task_id=task.task_id,
        iteration=iteration,
        raw_text=raw_text,
        diff=diff,
        target_files=target_files,
        parse_ok=parse_ok,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
