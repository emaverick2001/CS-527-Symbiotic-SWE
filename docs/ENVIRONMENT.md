# Environment And Reproducibility

## Local Environment

The default local workflow uses Poetry with an in-project virtual environment:

- Python: `3.11`
- Environment path: `.venv/`
- Dependency manifest: `pyproject.toml`
- Locked dependency versions: `poetry.lock`

## Container Environment

For a reproducible containerized setup, use the repository [Dockerfile](/Users/maver/Desktop/Coding Projects/AI/CS-527-Symbiotic-SWE/Dockerfile).

```bash
docker build -t symbiotic-swe .
docker run --rm -it symbiotic-swe
```

## Version Tracking

The scaffold tracks:

- Python version constraint
- dependency manifest and lockfile
- prompt version
- schema version

These values are surfaced in run metadata under `versions`.
