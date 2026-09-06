# Invoice Extraction Instructions

Extract invoice information exactly as represented in the document.

Rules:

- Never invent missing values.
- Use null when a field is not present.
- Preserve invoice and PO numbers exactly (keep leading zeros).
- Do not infer currency from the vendor's country.
- Preserve decimal amounts.
- Extract every visible line item.
- Use the invoice total, not subtotal, as total_amount.
