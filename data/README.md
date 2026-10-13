# Synthetic financial NER corpus

The pipeline generates this corpus locally through `src.financial_ner.dataset`. It contains no real personal or payment data. Values are placeholders designed for evaluation and include valid-looking but non-production test identifiers, synthetic names, and reserved example domains.

The generated JSONL records contain:

- the source sentence;
- character-level entity spans;
- token offsets;
- BIO labels.

Run `python -m src.cli pipeline --seed 42` to regenerate `outputs/dataset.jsonl`.
