from __future__ import annotations

from pathlib import Path

SCHEMA_VERSION = '0.1.0'
PROMPT_VERSION = 'v0'
PYTHON_VERSION_CONSTRAINT = '>=3.9, <3.12'
DEPENDENCY_MANIFEST = 'pyproject.toml'
DEPENDENCY_LOCKFILE = 'poetry.lock'


def version_manifest(project_root: Path) -> dict[str, str]:
    return {
        'python_version': PYTHON_VERSION_CONSTRAINT,
        'dependency_manifest': str(project_root / DEPENDENCY_MANIFEST),
        'dependency_lockfile': str(project_root / DEPENDENCY_LOCKFILE),
        'prompt_version': PROMPT_VERSION,
        'schema_version': SCHEMA_VERSION,
    }
