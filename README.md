# FolioIQ

Schema-driven document extraction for Python. Pass a **document**, a **YAML field spec**, and an optional **prompt** — get structured JSON back.

- **PyPI:** https://pypi.org/project/folioiq/
- **GitHub:** https://github.com/auspicious123/folioiq-sdk
- **License:** [MIT](LICENSE)

```bash
pip install folioiq
# or
uv add folioiq
```

---

## Install

### pip

```bash
pip install folioiq

# Azure OpenAI + Azure Document Intelligence (recommended)
pip install "folioiq[azure]"
```

### uv

```bash
uv add folioiq
uv add "folioiq[azure]"
```

Requires **Python 3.12+**.

---

## Configure credentials

Set these in your environment or a `.env` file in your project:

```bash
# Azure OpenAI (required for extract())
AZURE_API_KEY=...
AZURE_API_BASE=https://YOUR-RESOURCE.openai.azure.com/
AZURE_API_VERSION=2024-02-15-preview
model=your-azure-openai-deployment-name

# Azure Document Intelligence (required for scans / images)
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://YOUR-RESOURCE.cognitiveservices.azure.com/
AZURE_DOC_INTELLIGENCE_KEY=...
```

`model` is the **deployment name** from your Azure OpenAI resource (Portal → Deployments), not a FolioIQ-provided model. `AZURE_OPENAI_DEPLOYMENT` also works.

Digital PDFs with a text layer can run with OpenAI only. Scanned PDFs and images need Document Intelligence as well.

---

## Quick start

```python
from folioiq import DocumentExtractor

extractor = DocumentExtractor.from_env()

result = extractor.extract(
    document="invoice.pdf",
    spec="specs/invoice.yaml",
    instructions="specs/invoice.md",  # optional prompt
)

if result.is_valid:
    print(result.data)           # dict of extracted fields
else:
    print(result.validation_errors)
    print(result.metadata)       # parser, fallback, timings, etc.
```

`document` can be a **file path**, **bytes**, or a **file-like** object (PDF or common image types).

---

## YAML field spec

Define what to extract. Example:

```yaml
name: invoice
version: "1.0"

pipeline:
  mode: auto          # auto | explicit
  # parser: azure_di  # only when mode: explicit  (pymupdf | azure_di)

extraction:
  fields:
    invoice_number:
      type: string
      required: true
      description: Unique invoice id from the supplier.

    invoice_date:
      type: date
      required: true
      description: Date the invoice was issued.

    total_amount:
      type: number
      required: true
      description: Grand total (not subtotal).

    line_items:
      type: array
      required: false
      items:
        type: object
        fields:
          description: { type: string }
          quantity: { type: number }
          amount: { type: number }
```

Supported field types: `string`, `number`, `integer`, `boolean`, `date`, `datetime`, `array`, `object`.

### Force a parser

```yaml
pipeline:
  mode: explicit
  parser: azure_di   # or pymupdf
```

- **`auto`** (default): text PDF → PyMuPDF; scant / image → Azure Document Intelligence  
- On validation failure, FolioIQ retries once with the other parser when possible  

---

## Optional prompt / instructions

Pass extraction rules as Markdown **file path** or **inline string**:

```python
# Path to a .md file
result = extractor.extract(
    "po.pdf",
    spec="po.yaml",
    instructions="po_extraction.md",
)

# Inline prompt text
result = extractor.extract(
    "po.pdf",
    spec="po.yaml",
    instructions="Never invent values. Preserve PO numbers exactly. Use null when missing.",
)
```

If you omit `instructions` and a sibling file `your_spec.md` exists next to `your_spec.yaml`, it is loaded automatically.

---

## Result object

| Attribute | Meaning |
|-----------|---------|
| `result.data` | Extracted fields as a `dict` |
| `result.is_valid` | `True` if required fields / types pass validation |
| `result.validation_errors` | List of validation messages |
| `result.metadata` | `parser`, `fallback_used`, `llm`, `chars`, spec name/version, etc. |

---

## Other helpers

```python
# Load / inspect a spec without calling the LLM
spec = extractor.load_spec("invoice.yaml", instructions="invoice.md")

# Build the Pydantic model used for structured output
Model = extractor.build_model(spec)
```

---

## Links

| | |
|--|--|
| PyPI | https://pypi.org/project/folioiq/ |
| Latest release | https://pypi.org/project/folioiq/#history |
| Source | https://github.com/auspicious123/folioiq-sdk |
| Issues | https://github.com/auspicious123/folioiq-sdk/issues |

---

## License

MIT — see [LICENSE](LICENSE).

Maintainers: see [PUBLISH.md](PUBLISH.md) to release a new PyPI version.
