"""Pack layout

Each folder under packs/ is one eval case:

  document.pdf|jpg   — source file (from billing-validation samples)
  spec.yaml          — FolioIQ extraction spec
  instructions.md    — optional MD rules
  expected.json      — ground truth (nulls = unlabeled / skipped)

Run:

  folioiq-eval
  folioiq-eval tests/fixtures/packs/po
"""
