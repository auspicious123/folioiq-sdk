# FolioIQ — Build Plan

Provider-agnostic document extraction. Spec (YAML + optional MD) in → structured data out.

**Package:** `folioiq`  
**Promise:** consistent interface + providers + validation — not “always accurate.”

Keep it simple. Ship one phase at a time.

---

## Public API (target)

```python
from folioiq import DocumentExtractor

extractor = DocumentExtractor.from_env()
result = extractor.extract("invoice.pdf", spec="specs/invoice.yaml")

if result.is_valid:
    process(result.data)
```

---

## Phases

### Phase 0 — Scaffold ✅ done
- Repo layout, `pyproject.toml`, installable package
- Stub `DocumentExtractor` + `ExtractionResult`
- Config / env skeleton
- Extras: `[azure]` declared (deps unused until later)

**Done when:** `pip install -e .` and `from folioiq import DocumentExtractor` works.

### Phase 1 — Spec + models ✅ done
- Load YAML → field schema → Pydantic model (`load_spec`, `build_model`)
- Optional sibling `.md` instructions
- Example: `examples/invoice.yaml` + `invoice.md`
- No LLM yet (`extract()` still Phase 2)

### Phase 2 — Native parse + Azure OpenAI ✅ done
- PyMuPDF → embedded PDF text
- Prompt from YAML + MD
- Azure OpenAI structured output (`folioiq[azure]`)
- Digital PDF path only; inject `llm=` for tests / custom clients

```python
extractor = DocumentExtractor.from_env()
result = extractor.extract("invoice.pdf", spec="examples/invoice.yaml")
```

### Phase 3 — Azure DI + simple router ✅ done
- Auto: text PDF → `pymupdf`; scant/image → `azure_di`
- Explicit: `pipeline.mode: explicit` + `parser: pymupdf|azure_di`
- Inject `ocr=` for tests (same pattern as `llm=`)

### Phase 4 — Validation + one fallback ✅ done
- Required / type checks via `validate_extraction`
- One retry with the alternate parser (`pymupdf` ↔ `azure_di`)
- `is_valid`, `validation_errors`, `metadata.fallback_used`

### Phase 5 — Fixtures / eval ✅ done
- Packs under `tests/fixtures/packs/{po,so,contract,dr}`
- `expected.json` ground truth (dr pack placeholder until labeled)
- `python -m folioiq.eval [pack_dir]` or `folioiq-eval`
- Field accuracy scoring (loose string / number match)

### Later (only if needed)
- OpenAI / Bedrock / Textract / Docling extras
- Rich layout IR, business-rule engine, async API

---

## V1 providers (hard cut)

| In | Out for now |
|----|-------------|
| PyMuPDF | Docling |
| Azure DI | Textract |
| Azure OpenAI | Other LLMs |

---

## Rules

1. Don’t add providers until the previous phase works.
2. One YAML dialect only (new nested `fields` style).
3. Secrets in env only.
4. Prefer small files and clear names over deep abstractions.
5. Stop after each phase and review before the next.
