# Publish FolioIQ

Bump `version` in `pyproject.toml` first (same version for TestPyPI and PyPI).

Tokens: `~/.pypirc` (`[testpypi]` and `[pypi]` — separate tokens).

```bash
cd "/Users/shubhamk/F/J/Gen/Billing Validation/folioiq-sdk"
source .venv/bin/activate

rm -rf dist/ build/
python -m build
twine check dist/*

# 1. TestPyPI
twine upload --repository testpypi dist/*

# 2. PyPI
twine upload dist/*
```

- TestPyPI: https://test.pypi.org/project/folioiq/
- PyPI: https://pypi.org/project/folioiq/
