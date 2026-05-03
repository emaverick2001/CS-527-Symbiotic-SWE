from __future__ import annotations

import ast
import re
import textwrap
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set

from symbiotic_swe.contracts import PatchContract, ProgramSlice


def _changed_files_from_diff(diff: str) -> List[str]:
    files = []
    for line in diff.splitlines():
        if line.startswith('diff --git '):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[2].removeprefix('a/'))
        elif line.startswith('--- a/'):
            files.append(line.removeprefix('--- a/'))
    return list(dict.fromkeys(files))


def _changed_line_ranges(diff: str, target_file: str) -> List[tuple]:
    ranges = []
    in_file = False
    for line in diff.splitlines():
        if line.startswith('diff --git'):
            in_file = target_file in line
        elif line.startswith('--- '):
            # handles both '--- a/path' and '--- path' without diff --git header
            in_file = target_file in line
        elif in_file and line.startswith('@@'):
            m = re.search(r'\+(\d+)(?:,(\d+))?', line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2)) if m.group(2) else 1
                ranges.append((start, start + count))
    return ranges


def _functions_at_lines(source: str, line_ranges: List[tuple]) -> Dict[str, str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    lines = source.splitlines()
    changed_lines: Set[int] = set()
    for start, end in line_ranges:
        changed_lines |= set(range(start, end + 1))

    funcs: Dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        end_line = getattr(node, 'end_lineno', node.lineno)
        node_lines = set(range(node.lineno, end_line + 1))
        if node_lines & changed_lines:
            snippet = '\n'.join(lines[node.lineno - 1:end_line])
            funcs[node.name] = textwrap.dedent(snippet)
    return funcs


def _extract_path_conditions(source: str) -> List[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    conditions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            conditions.append(ast.unparse(node.test))
        elif isinstance(node, ast.While):
            conditions.append(ast.unparse(node.test))
    return conditions


def _extract_variables(source: str) -> List[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
    return sorted(names)


def slice_impact(
    patch: PatchContract,
    repo_path: Path,
    task_id: Optional[str] = None,
) -> ProgramSlice:
    slice_id = str(uuid.uuid4())[:8]
    tid = task_id or patch.task_id

    changed_files = _changed_files_from_diff(patch.diff)
    source_snippets: Dict[str, str] = {}
    target_functions: List[str] = []
    modified_nodes: List[str] = []
    all_conditions: List[str] = []
    all_variables: List[str] = []

    for rel_path in changed_files:
        fpath = repo_path / rel_path
        if not fpath.exists() or not fpath.suffix == '.py':
            continue
        try:
            source = fpath.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue

        line_ranges = _changed_line_ranges(patch.diff, rel_path)
        funcs = _functions_at_lines(source, line_ranges)

        for fname, fsource in funcs.items():
            qualified = f'{rel_path}::{fname}'
            target_functions.append(fname)
            modified_nodes.append(qualified)
            source_snippets[qualified] = fsource
            all_conditions.extend(_extract_path_conditions(fsource))
            all_variables.extend(_extract_variables(fsource))

    return ProgramSlice(
        slice_id=slice_id,
        task_id=tid,
        iteration=patch.iteration,
        target_functions=list(dict.fromkeys(target_functions)),
        modified_nodes=list(dict.fromkeys(modified_nodes)),
        affected_variables=list(dict.fromkeys(all_variables)),
        path_conditions=list(dict.fromkeys(all_conditions)),
        related_tests=list(patch.target_files),
        source_snippets=source_snippets,
    )
