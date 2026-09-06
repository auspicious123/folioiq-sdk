# FolioIQ

[![PyPI](https://img.shields.io/badge/pypi-folioiq-blue)](https://pypi.org/project/folioiq/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Schema-driven document extraction. YAML spec (+ optional MD) in → structured data out.

```python
from folioiq import DocumentExtractor

extractor = DocumentExtractor.from_env()
result = extractor.extract("invoice.pdf", spec="examples/invoice.yaml")

if result.is_valid:
    print(result.data)
else:
    print(result.validation_errors)
```

## Install

```bash
pip install folioiq
pip install "folioiq[azure]"   # Azure OpenAI + Document Intelligence
```

Or from source:

```bash
git clone https://github.com/auspicious123/folioiq-sdk.git
cd folioiq-sdk
python -m venv .venv && source .venv/bin/activate
pip install -e ".[azure,dev]"
cp .env.example .env   # fill Azure vars
```

## Spec only (no LLM)

```python
spec = extractor.load_spec("examples/invoice.yaml")
Model = extractor.build_model(spec)
```

## Pipeline override (YAML)

```yaml
pipeline:
  mode: explicit
  parser: azure_di   # or pymupdf
```

## Eval

```bash
pip install -e ".[azure,dev]"
folioiq-eval                         # all fixture packs
folioiq-eval tests/fixtures/packs/po
```

## License

MIT — see [LICENSE](LICENSE).

See [PLAN.md](PLAN.md) for design phases.
