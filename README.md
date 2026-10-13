# Privacy-Preserving Financial NER

**Privacy-Preserving Named Entity Recognition for Automated PCI/PII Detection in Financial Text**

This project implements and evaluates a domain-focused Named Entity Recognition (NER) system for financial text. It detects sensitive entities such as names, emails, phone numbers, card-like values, account numbers, tax identifiers, addresses, organizations and transaction references, then redacts them before text is shared with downstream analytics or language models.

The work is designed for the NLP activity requirements:

- syllabus topic: Named Entity Recognition;
- real-world application/API: a local JSON HTTP API for financial-message redaction;
- conceptual architecture: rule baseline, context-aware averaged perceptron, and a privacy-first hybrid detector;
- implementation: deterministic synthetic financial corpus with BIO annotations;
- evaluation: token accuracy, entity-level precision, recall and F1, plus per-entity analysis;
- comparison: deterministic rules vs learned model vs hybrid system;
- communication: technical report and presentation artifacts in `reports/`.

## Why the topic is distinctive

Generic NER projects usually stop at detecting people and locations. Financial compliance needs both contextual language understanding and deterministic validation. A card number must pass a Luhn check, while an email or transaction reference may be recognized from surrounding context. The hybrid architecture combines these strengths and enforces a privacy boundary: the detector returns masked entity metadata instead of requiring raw values to be sent to a language model.

## Run the project

Requires Python 3.10+ and no third-party packages.

```bash
python -m src.cli pipeline --seed 42
python -m src.cli demo
python -m src.api
```

The pipeline writes reproducible outputs to `outputs/`:

- `metrics.json` — overall and per-entity metrics;
- `metrics.csv` — comparison table;
- `sample_predictions.json` — redaction examples;
- `dataset.jsonl` — generated, synthetic, BIO-ready examples.

The API runs at `http://127.0.0.1:8080`.

```bash
curl http://127.0.0.1:8080/health
curl -X POST http://127.0.0.1:8080/redact ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Maya Rao emailed maya.rao@example.com about transaction TXN-48291.\"}"
```

On PowerShell, use `Invoke-RestMethod` if `curl` resolves to the PowerShell alias.

## Project layout

```text
src/financial_ner/     tokenization, synthetic data, rules, ML model, metrics
src/cli.py             pipeline and demo command line interface
src/api.py             dependency-free JSON HTTP API
data/                  generated corpus destination and data documentation
reports/               Markdown report, DOCX report and PPTX presentation
tests/                 standard-library regression tests
tools/                 document artifact generator
```

## Important safety note

All examples are synthetic. The repository must not be connected to real cardholder data without a security review, access control, retention policy, and a local scanning boundary. The API returns entity spans and masked text; it is not a payment processor or a compliance certification.

## Academic deliverables

- `reports/Privacy_Preserving_Financial_NER_Report.docx`
- `reports/Privacy_Preserving_Financial_NER_Presentation.pptx`
- `reports/technical_report.md`

The report and presentation are aligned with the supplied B.M.S. College of Engineering AAT templates: course heading, topic, submitted-by placeholders, Semester & Section 7C, faculty-in-charge, agenda, the ten report sections, results, discussion, references and thank-you slide. The report includes the conceptual review, architecture, preprocessing, training workflow, evaluation methodology, results, limitations and conclusion. The presentation is organized for an oral explanation of the same work.
