from __future__ import annotations

import re
import sys
import time as _time
import uuid
from pathlib import Path
from typing import List, Optional

from symbiotic_swe.contracts import (
    CanonicalTask,
    CritiqueContract,
    PatchContract,
    RetrievedContext,
)
from symbiotic_swe.context_selection.selector import load_context_source
from symbiotic_swe.patch_generation.prompt_builder import SYSTEM_PROMPT, build_patch_prompt


MODEL = 'gpt-5.4-mini'
PROVIDER = 'openai'
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
            old_count = sum(1 for line in hunk if line.startswith(' ') or line.startswith('-'))
            new_count = sum(1 for line in hunk if line.startswith(' ') or line.startswith('+'))
            result.append(f'@@ -{old_start},{old_count} +{new_start},{new_count} {m.group(5).lstrip()}')
            result.extend(hunk)
        else:
            result.append(line)
            i += 1
    return '\n'.join(result) + '\n'


def _drop_prompt_artifact_lines(diff: str) -> str:
    """Remove prompt-only context markers if a model copied them into a hunk."""
    artifact_markers = (
        '# ... (truncated before)',
        '# ... (truncated after)',
        '# ... (truncated)',
        '# Exact checked-out source lines',
    )
    cleaned: List[str] = []
    for line in diff.splitlines():
        payload = line[1:] if line[:1] in {' ', '+', '-'} else line
        if any(marker in payload for marker in artifact_markers):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned) + '\n'


def _ensure_git_headers(diff: str) -> str:
    lines = diff.splitlines()
    if not lines or lines[0].startswith('diff --git '):
        return diff

    result: List[str] = []
    i = 0
    while i < len(lines):
        if (
            lines[i].startswith('--- a/')
            and i + 1 < len(lines)
            and lines[i + 1].startswith('+++ b/')
        ):
            old_path = lines[i].removeprefix('--- ')
            new_path = lines[i + 1].removeprefix('+++ ')
            result.append(f'diff --git {old_path} {new_path}')
        result.append(lines[i])
        i += 1
    return '\n'.join(result) + '\n'


def _extract_diff(raw_text: str) -> str:
    # Collect all ```diff blocks; use the last non-empty one.
    candidates = re.findall(r'```diff\s*\n(.*?)```', raw_text, re.DOTALL)
    candidates = [c.strip() for c in candidates if c.strip()]
    if candidates:
        return _ensure_git_headers(_fix_hunk_counts(_drop_prompt_artifact_lines(candidates[-1])))
    # Fallback: unnamed code block that looks like a diff
    blocks = re.findall(r'```\s*\n(.*?)```', raw_text, re.DOTALL)
    for block in reversed(blocks):
        block = block.strip()
        if block.startswith(('diff --git', '--- ', '@@ ', '+')):
            return _ensure_git_headers(_fix_hunk_counts(_drop_prompt_artifact_lines(block)))
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


def _usage_value(usage: object, *names: str) -> int:
    for name in names:
        value = getattr(usage, name, None)
        if isinstance(value, int):
            return value
    return 0


def _call_anthropic(
    *,
    messages: List[dict],
    api_key: Optional[str],
    model: str,
) -> tuple[str, int, int]:
    import anthropic as _anthropic

    client = _anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return (
        response.content[0].text,
        _usage_value(response.usage, 'input_tokens'),
        _usage_value(response.usage, 'output_tokens'),
    )


def _call_openai(
    *,
    messages: List[dict],
    api_key: Optional[str],
    model: str,
) -> tuple[str, int, int]:
    from openai import OpenAI

    user_content = '\n\n'.join(str(message.get('content', '')) for message in messages if message.get('role') == 'user')
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=user_content,
        max_output_tokens=MAX_TOKENS,
    )
    raw_text = getattr(response, 'output_text', '') or ''
    if not raw_text:
        parts: list[str] = []
        for item in getattr(response, 'output', []) or []:
            for content in getattr(item, 'content', []) or []:
                text = getattr(content, 'text', None)
                if text:
                    parts.append(text)
        raw_text = '\n'.join(parts)
    usage = getattr(response, 'usage', None)
    return (
        raw_text,
        _usage_value(usage, 'input_tokens'),
        _usage_value(usage, 'output_tokens'),
    )


def _call_model(
    *,
    provider: str,
    messages: List[dict],
    api_key: Optional[str],
    model: str,
) -> tuple[str, int, int]:
    if provider == 'anthropic':
        return _call_anthropic(messages=messages, api_key=api_key, model=model)
    if provider == 'openai':
        return _call_openai(messages=messages, api_key=api_key, model=model)
    raise ValueError(f'unsupported model provider: {provider}')


def generate_patch(
    task: CanonicalTask,
    context: RetrievedContext,
    iteration: int,
    critique: Optional[CritiqueContract] = None,
    repo_path: Optional[Path] = None,
    api_key: Optional[str] = None,
    model: str = MODEL,
    provider: str = PROVIDER,
) -> PatchContract:
    patch_id = str(uuid.uuid4())[:8]
    context_source = load_context_source(task, context, repo_path)

    messages = build_patch_prompt(task, context_source, iteration, critique)

    raw_text = ''
    prompt_tokens = 0
    completion_tokens = 0
    last_exc: Optional[Exception] = None

    for attempt in range(3):
        try:
            raw_text, prompt_tokens, completion_tokens = _call_model(
                provider=provider,
                messages=messages,
                api_key=api_key,
                model=model,
            )
            last_exc = None
            break
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                wait = 2 ** attempt
                print(f'  [generator retry {attempt + 1}/3 in {wait}s] {exc}', file=sys.stderr)
                _time.sleep(wait)
            else:
                print(f'  [generator error] {exc}', file=sys.stderr)

    if last_exc is not None:
        return PatchContract(
            patch_id=patch_id,
            task_id=task.task_id,
            iteration=iteration,
            raw_text='',
            diff='',
            errors=[str(last_exc)],
            model=f'{provider}:{model}',
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
        model=f'{provider}:{model}',
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )


def _file_repair_context(repo_path: Path, target_files: list[str], limit: int = 24_000) -> str:
    chunks: list[str] = []
    remaining = limit
    for rel_path in target_files:
        path = repo_path / rel_path
        if not path.exists() or not path.is_file():
            continue
        source = path.read_text(encoding='utf-8', errors='replace')
        numbered = '\n'.join(f'{idx:5d}: {line}' for idx, line in enumerate(source.splitlines(), start=1))
        chunk = f'# File: {rel_path}\n{numbered}\n'
        if len(chunk) > remaining:
            chunk = chunk[:remaining]
        chunks.append(chunk)
        remaining -= len(chunk)
        if remaining <= 0:
            break
    return '\n\n'.join(chunks)


def repair_patch_application(
    *,
    task: CanonicalTask,
    failed_patch: PatchContract,
    apply_error: str,
    repo_path: Path,
    api_key: Optional[str] = None,
    model: str = MODEL,
    provider: str = PROVIDER,
) -> PatchContract:
    """Ask the model to rewrite a parsed patch against exact checked-out file content."""
    patch_id = str(uuid.uuid4())[:8]
    target_files = failed_patch.target_files or _changed_files(failed_patch.diff)
    file_context = _file_repair_context(repo_path, target_files)
    if not file_context:
        return failed_patch.model_copy(update={
            'patch_id': patch_id,
            'errors': failed_patch.errors + ['patch repair skipped: no target file context available'],
        })

    user_content = f"""\
## Bug Report
{task.bug_description}

## Failing Tests
{chr(10).join(f'- {t}' for t in task.failing_tests)}

## Patch Apply Error
{apply_error}

## Failed Patch
```diff
{failed_patch.diff}
```

## Exact Checked-Out Target Files
Line numbers are for reference only. Do not include line-number prefixes in the patch.

```python
{file_context}
```

Rewrite the failed patch so it applies cleanly to the exact checked-out files above.
Return exactly one git-style unified diff in a single ```diff code block.
"""

    raw_text = ''
    prompt_tokens = 0
    completion_tokens = 0
    last_exc: Optional[Exception] = None
    messages = [{'role': 'user', 'content': user_content}]
    for attempt in range(2):
        try:
            raw_text, prompt_tokens, completion_tokens = _call_model(
                provider=provider,
                messages=messages,
                api_key=api_key,
                model=model,
            )
            last_exc = None
            break
        except Exception as exc:
            last_exc = exc
            if attempt < 1:
                print(f'  [patch repair retry 1/2] {exc}', file=sys.stderr)
                _time.sleep(1)
            else:
                print(f'  [patch repair error] {exc}', file=sys.stderr)

    if last_exc is not None:
        return failed_patch.model_copy(update={
            'patch_id': patch_id,
            'errors': failed_patch.errors + [f'patch repair failed: {last_exc}'],
        })

    diff = _extract_diff(raw_text)
    parse_ok = bool(diff.strip())
    repaired_files = _changed_files(diff) if parse_ok else []
    return PatchContract(
        patch_id=patch_id,
        task_id=task.task_id,
        iteration=failed_patch.iteration,
        raw_text=raw_text,
        diff=diff,
        target_files=repaired_files,
        parse_ok=parse_ok,
        model=f'{provider}:{model}:repair',
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        errors=[] if parse_ok else ['patch repair produced no parseable diff'],
    )
