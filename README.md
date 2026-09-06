# FolioIQ

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
cd folioiq-sdk
python -m venv .venv && source .venv/bin/activate
pip install -e ".[azure,dev]"
cp .env.example .env   # fill Azure OpenAI vars
```

## Spec only (no LLM)

```python
spec = extractor.load_spec("examples/invoice.yaml")
Model = extractor.build_model(spec)
```

## Status

- Phase 0–1: package + YAML → Pydantic  
- Phase 2: digital PDF text + Azure OpenAI  
- Phase 3: auto router + Azure Document Intelligence for scans/images  
- Phase 4: required-field validation + one alternate-parser fallback  
- Phase 5: fixture packs + `folioiq-eval`  

### Eval

```bash
pip install -e ".[azure,dev]"
# with Azure env configured:
folioiq-eval                              # all packs
folioiq-eval tests/fixtures/packs/po      # one pack
```

See [PLAN.md](PLAN.md).

### Pipeline override (YAML)

```yaml
pipeline:
  mode: explicit
  parser: azure_di   # or pymupdf
```
