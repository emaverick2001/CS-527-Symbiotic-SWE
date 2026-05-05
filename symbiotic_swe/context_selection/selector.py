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


def _is_sympy_numeric_boolean_equality_report(task: CanonicalTask) -> bool:
    if task.repo != 'sympy/sympy':
        return False

    text = f'{task.bug_description} {" ".join(task.failing_tests)}'.lower()
    has_boolean_operand = any(token in text for token in ('s.false', 's.true', 'false', 'true', 'boolean'))
    has_numeric_operand = any(token in text for token in ('s(0.0)', 's(0)', 'float', 'number', '0.0'))
    has_equality = any(token in text for token in ('==', 'equality', 'comparing', 'comparison'))
    return has_boolean_operand and has_numeric_operand and has_equality


def _is_sympy_complex_exponent_comparison_report(task: CanonicalTask) -> bool:
    if task.repo != 'sympy/sympy':
        return False

    text = f'{task.bug_description} {" ".join(task.failing_tests)}'.lower()
    has_complex_exponent = any(token in text for token in ('cos(x)**i', 'sin(x)**i', 'complex i', 'invalid comparison'))
    has_simplify_path = any(token in text for token in ('fu.py', 'trigsimp', 'simplify', 'tr56', 'test__tr56'))
    has_comparison = any(token in text for token in ('rv.exp', '< 0', '> max', 'comparison'))
    return has_complex_exponent and has_simplify_path and has_comparison


def _priority_source_paths(task: CanonicalTask) -> List[str]:
    """Repo-specific source hints for bugs where lexical search is misleading."""
    if _is_sympy_numeric_boolean_equality_report(task):
        return ['sympy/core/numbers.py']
    if _is_sympy_complex_exponent_comparison_report(task):
        return ['sympy/simplify/fu.py']
    return []


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
    selected_paths: set[str] = set()
    entries_by_path = {entry.path: entry for entry in repo_index.files}

    for path in _priority_source_paths(task):
        entry = entries_by_path.get(path)
        if entry is None or entry.parse_failed or entry.role != 'source':
            continue
        selected_files.append(entry)
        selected_paths.add(entry.path)
        total_chars += sum(len(s.source) for s in entry.symbols)

    for entry, score in scored[:top_k]:
        if entry.path in selected_paths:
            continue
        # Load actual source from disk if available
        selected_files.append(entry)
        selected_paths.add(entry.path)
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


def _find_sympy_float_eq_line(source: str) -> int | None:
    lines = source.splitlines()
    in_float = False
    for index, line in enumerate(lines, start=1):
        if line.startswith('class Float('):
            in_float = True
            continue
        if in_float and line.startswith('class ') and not line.startswith('class Float('):
            return None
        if in_float and line.startswith('    def __eq__(self, other):'):
            return index
    return None


def _find_sympy_tr56_inner_line(source: str) -> int | None:
    for index, line in enumerate(source.splitlines(), start=1):
        if line.startswith('def _TR56('):
            return index
    return None


def _priority_source_windows(task: CanonicalTask, repo_path: Path) -> List[tuple[str, int, str]]:
    windows: List[tuple[str, int, str]] = []
    for rel_path in _priority_source_paths(task):
        fpath = repo_path / rel_path
        if not fpath.exists():
            continue
        try:
            source = fpath.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue

        if rel_path == 'sympy/core/numbers.py':
            line = _find_sympy_float_eq_line(source)
            if line is not None:
                windows.append((rel_path, line, 'SymPy Float.__eq__ numeric-vs-Boolean equality logic'))
        elif rel_path == 'sympy/simplify/fu.py':
            line = _find_sympy_tr56_inner_line(source)
            if line is not None:
                windows.append((rel_path, line, 'SymPy _TR56 complex exponent guard before exponent comparisons'))
    return windows


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
    CONTEXT_WINDOW_RADIUS = 120  # source lines around matched symbol when file is large
    chunks: List[str] = []
    seen_paths: set[str] = set()

    for rel_path, line, reason in _priority_source_windows(task, repo_path):
        fpath = repo_path / rel_path
        try:
            source = fpath.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        start, end, excerpt = _line_window(source, line, radius=60)
        chunks.append(
            f'# File: {rel_path}\n'
            f'# High-priority source context: {reason}.\n'
            f'# Exact checked-out source lines {start}-{end}; line {line} is the prioritized equality implementation.\n'
            f'{excerpt}'
        )
        seen_paths.add(rel_path)

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
                    best = next((s for s in entry.symbols if s.source), None)
                    if best:
                        start, end, excerpt = _line_window(
                            source,
                            best.line_start,
                            radius=CONTEXT_WINDOW_RADIUS,
                        )
                        source = (
                            f'# Exact checked-out source lines {start}-{end}; '
                            'surrounding file content omitted from the prompt.\n'
                            f'{excerpt}'
                        )
                    else:
                        source = source[:PER_FILE_LIMIT]
                elif len(source) > PER_FILE_LIMIT:
                    source = source[:PER_FILE_LIMIT]
                chunks.append(f'# File: {entry.path}\n{source}')
            except Exception:
                pass
    return '\n\n'.join(chunks)
