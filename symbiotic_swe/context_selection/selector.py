from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from symbiotic_swe.contracts import CanonicalTask, RepoFileEntry, RepoIndex, RetrievedContext


def _tokenize(text: str) -> set:
    return set(re.findall(r'\b[a-zA-Z_]\w*\b', text.lower()))


def _score_file(entry: RepoFileEntry, query_tokens: set) -> float:
    if entry.parse_failed:
        return 0.0
    if entry.role == 'test':
        return 0.0

    file_tokens = _tokenize(entry.path)
    symbol_names_lower = {s.name.lower() for s in entry.symbols}
    symbol_tokens = _tokenize(' '.join(s.name for s in entry.symbols))
    import_tokens = _tokenize(' '.join(entry.imports))
    combined = file_tokens | symbol_tokens | import_tokens

    overlap = len(query_tokens & combined)
    if not combined:
        return 0.0
    base = overlap / (len(combined) ** 0.5)

    # Strongly boost files that *define* symbols the query mentions by name
    exact_symbol_hits = len(query_tokens & symbol_names_lower)
    return base + 4.0 * exact_symbol_hits


def select_context(
    task: CanonicalTask,
    repo_index: RepoIndex,
    top_k: int = 10,
    max_chars: int = 60_000,
) -> RetrievedContext:
    query = f'{task.bug_description} {" ".join(task.failing_tests)}'
    query_tokens = _tokenize(query)

    # Also add tokens from failing test names to boost relevant files
    test_module_tokens: set = set()
    for t in task.failing_tests:
        parts = t.replace('::', '/').split('/')
        for p in parts:
            test_module_tokens |= _tokenize(p)
    query_tokens |= test_module_tokens

    scored = [
        (entry, _score_file(entry, query_tokens))
        for entry in repo_index.files
        if not entry.parse_failed and entry.role == 'source'
    ]
    scored.sort(key=lambda x: -x[1])

    selected_files: List[RepoFileEntry] = []
    total_chars = 0
    for entry, score in scored[:top_k]:
        # Load actual source from disk if available
        selected_files.append(entry)
        total_chars += sum(len(s.source) for s in entry.symbols)
        if total_chars >= max_chars:
            break

    all_symbols = [s for f in selected_files for s in f.symbols]

    return RetrievedContext(
        task_id=task.task_id,
        query=query,
        files=selected_files,
        symbols=all_symbols[:100],
        total_chars=total_chars,
    )


def _traceback_locations(task: CanonicalTask) -> List[tuple[str, int]]:
    text = '\n'.join([task.bug_description, *task.execution_trace])
    locations: List[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    for match in re.finditer(r'([A-Za-z0-9_./-]+\.py):(\d+)', text):
        path = match.group(1).lstrip('./')
        line = int(match.group(2))
        key = (path, line)
        if key not in seen:
            locations.append(key)
            seen.add(key)
    return locations


def _line_window(source: str, center_line: int, radius: int = 45) -> tuple[int, int, str]:
    lines = source.splitlines()
    start = max(1, center_line - radius)
    end = min(len(lines), center_line + radius)
    excerpt = '\n'.join(lines[start - 1:end])
    return start, end, excerpt


def load_context_source(
    task: CanonicalTask,
    context: RetrievedContext,
    repo_path: Optional[Path],
) -> str:
    if repo_path is None:
        return '\n\n'.join(
            f'# {s.file}:{s.line_start}\n{s.source}'
            for s in context.symbols
            if s.source
        )

    PER_FILE_LIMIT = 8_000
    CONTEXT_WINDOW = 3_000  # chars around matched symbol when file is large
    chunks: List[str] = []
    seen_paths: set[str] = set()

    for rel_path, line in _traceback_locations(task):
        fpath = repo_path / rel_path
        if not fpath.exists():
            continue
        try:
            source = fpath.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        start, end, excerpt = _line_window(source, line)
        chunks.append(
            f'# File: {rel_path}\n'
            f'# Exact checked-out source lines {start}-{end}; line {line} is from the traceback.\n'
            f'{excerpt}'
        )
        seen_paths.add(rel_path)

    for entry in context.files:
        if entry.path in seen_paths:
            continue
        fpath = repo_path / entry.path
        if fpath.exists():
            try:
                source = fpath.read_text(encoding='utf-8', errors='replace')
                if len(source) > PER_FILE_LIMIT and entry.symbols:
                    # Extract a window around the most relevant symbol (first with source)
                    lines = source.splitlines(keepends=True)
                    best = next((s for s in entry.symbols if s.source), None)
                    if best:
                        # Convert line number to char offset
                        start_line = max(0, best.line_start - 1)
                        end_line = min(len(lines), getattr(best, 'line_end', best.line_start))
                        char_start = sum(len(line) for line in lines[:start_line])
                        char_end = sum(len(line) for line in lines[:end_line])
                        # Pad to CONTEXT_WINDOW on each side
                        pad = max(0, (CONTEXT_WINDOW - (char_end - char_start)) // 2)
                        c_start = max(0, char_start - pad)
                        c_end = min(len(source), char_end + pad)
                        excerpt = source[c_start:c_end]
                        prefix = '# ... (truncated before)\n' if c_start > 0 else ''
                        suffix = '\n# ... (truncated after)' if c_end < len(source) else ''
                        source = prefix + excerpt + suffix
                    else:
                        source = source[:PER_FILE_LIMIT] + '\n# ... (truncated)'
                elif len(source) > PER_FILE_LIMIT:
                    source = source[:PER_FILE_LIMIT] + '\n# ... (truncated)'
                chunks.append(f'# File: {entry.path}\n{source}')
            except Exception:
                pass
    return '\n\n'.join(chunks)
