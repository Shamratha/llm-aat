# Privacy-Preserving Named Entity Recognition for Automated PCI/PII Detection in Financial Text

**Course activity:** Topic Exploration, Implementation, Validation and Presentation
**NLP topic:** Named Entity Recognition (NER)
**Team:** To be completed by the two student members
**Application domain:** Financial services, privacy operations and payment security
**Repository:** https://github.com/Shamratha/llm-aat

## Abstract

Financial institutions process customer communications, payment events, support cases and operational logs that may contain personally identifiable information (PII) or payment-card information. Sending these texts directly to analytics systems or language models can create an avoidable privacy risk. This project implements a privacy-preserving Named Entity Recognition system that detects sensitive entities, validates structured payment identifiers, and returns redacted text with evidence metadata.

The project compares three approaches: a deterministic rules baseline, an averaged-perceptron contextual NER model trained on a synthetic financial corpus, and a hybrid detector that combines model predictions with validated rules. The corpus contains BIO annotations for PERSON, EMAIL, PHONE, CARD_NUMBER, ACCOUNT_NUMBER, TAX_ID, ADDRESS, TRANSACTION_ID and ORGANIZATION. Evaluation uses exact entity-level precision, recall and F1, together with token accuracy. On the reproducible 600-example test protocol, the rules baseline achieved an F1 of 0.7696, while both the averaged perceptron and hybrid system achieved an F1 of 0.9960. The result shows why context-aware learning is useful for unstructured entities and why deterministic checks remain important for structured financial identifiers.

## 1. Topic exploration and relevance

### 1.1 Chosen NLP topic

The selected syllabus topic is **Named Entity Recognition**. NER assigns a semantic label to a span of text, for example identifying `Maya Rao` as a person or `maya.rao@example.com` as an email address. The task is commonly represented with the BIO tagging scheme:

```text
Maya       B-PERSON
Rao        I-PERSON
emailed    O
maya...    B-EMAIL
```

### 1.2 Real-world application

The selected application is a compliance data-loss prevention service for financial organizations. It can be placed before a language model, ticketing system, monitoring platform or data warehouse. A typical request is:

```text
Customer Maya Rao emailed maya.rao@example.com about card 4111 1111 1111 1111.
```

The service returns:

```text
Customer [PERSON] emailed [EMAIL] about card [CARD_NUMBER].
```

It also returns masked spans, labels, character offsets, detection source and a privacy note. In a production system, raw values would remain inside a local or controlled scanning boundary.

### 1.3 Why this is a meaningful NER problem

Generic NER demonstrations often focus on people, organizations and locations. Financial text adds domain-specific requirements:

1. Structured identifiers such as card numbers require deterministic validation.
2. A value’s meaning depends on its surrounding words; `AC-48291037` is an account only in the right context.
3. False negatives can expose sensitive data, while false positives create operational noise.
4. The output must be useful for redaction and audit evidence, not only classification.
5. Synthetic data is preferable for a classroom demonstration because it avoids handling real cardholder data.

## 2. Literature and conceptual review

NER has evolved from hand-written dictionaries and regular expressions to statistical sequence models and contextual neural language models. Feature-based sequence models use token shape, prefixes, suffixes and neighboring words. Neural approaches learn distributed representations and use surrounding context to resolve ambiguity. Transformer-based models such as BERT are widely used for token classification because self-attention lets each token use information from the whole sentence.

This project intentionally implements an interpretable, dependency-free averaged perceptron rather than downloading a large pretrained model. It makes the data flow, features and update rule visible for an academic activity and keeps the experiment reproducible on a normal laptop. The hybrid design still reflects a production pattern: use learned context for language and deterministic validators for high-confidence structured data.

### 2.1 Architecture and data flow

```text
Synthetic financial text
        |
        v
Tokenizer + character offsets
        |
        +--> Regex validators + Luhn check ------+
        |                                          |
        +--> Contextual averaged perceptron -------+--> overlap resolver
                                                   |
                                                   v
                                    entities + masked redaction + evidence
```

### 2.2 Model features

For each token, the perceptron uses:

- lower-cased token;
- token shape, such as `Xx-dd`;
- two-character prefix and suffix;
- previous and next two tokens;
- a three-token context feature;
- digit, uppercase and title-case flags;
- the previous predicted BIO label.

The model is trained with an averaged online perceptron update. The averaging reduces the impact of individual examples and makes the final model less sensitive to the last update sequence.

## 3. Dataset and preprocessing

The corpus is generated deterministically by `src/financial_ner/dataset.py`. It contains 600 synthetic examples with no real customer information. Templates represent payment support, KYC, refunds, billing addresses, transaction reviews, privacy assessments and operational escalations.

### 3.1 Entity categories

| Label | Example purpose |
|---|---|
| PERSON | Customer or staff name |
| EMAIL | Contact address |
| PHONE | Contact number |
| CARD_NUMBER | Payment-card-like value validated with Luhn |
| ACCOUNT_NUMBER | Synthetic account reference |
| TAX_ID | Synthetic tax or national identifier |
| ADDRESS | Billing or residence address |
| TRANSACTION_ID | Payment or case reference |
| ORGANIZATION | Financial institution or processor |

### 3.2 Preprocessing steps

1. Generate a sentence from a template and synthetic values.
2. Record character-level entity spans before tokenization.
3. Tokenize while preserving each token’s start and end offsets.
4. Convert spans into BIO labels.
5. Shuffle with seed `42`.
6. Split into 70% train, 15% development and 15% test.

The resulting split is 420 training examples, 90 development examples and 90 test examples. The development set is reserved for future hyperparameter tuning; the current demonstration uses the fixed eight-epoch configuration so that the comparison remains simple and reproducible.

## 4. Implementation methodology

### 4.1 Rules baseline

The baseline recognizes structured patterns for email, phone, tax IDs, account references and transaction references. Card-like values are accepted only when their digit sequence passes the Luhn checksum. It also recognizes addresses when they occur after an address cue. The baseline intentionally does not use a name or organization dictionary, which exposes the limitation of pattern-only detection for contextual entities.

### 4.2 Averaged perceptron

The model predicts one BIO label per token. At each position it scores all possible labels using the feature vector and the current weights. If the predicted label differs from the gold label, weights for the gold features are increased and weights for the predicted features are decreased. At the end of training, weights are averaged over update steps.

### 4.3 Hybrid detector

The hybrid detector first keeps validated, non-overlapping structured matches from the rules layer and then adds non-overlapping entities from the learned model. This makes the data path auditable: deterministic rules can be inspected independently, while the learned component covers PERSON, ORGANIZATION and contextual ADDRESS cases.

### 4.4 Privacy-preserving API

`src/api.py` exposes a local JSON API:

- `GET /health` checks service availability;
- `GET /demo` returns a standard synthetic example;
- `POST /redact` accepts `{ "text": "...", "method": "hybrid" }`;
- supported methods are `rules`, `model` and `hybrid`.

The API response returns redacted text and masked entity metadata rather than asking a language model to inspect the raw value. The local server binds to `127.0.0.1`.

## 5. Experimental setup and metrics

All reported values are generated with:

```bash
python -m src.cli pipeline --seed 42 --size 600
```

### 5.1 Entity-level metrics

An entity is counted as correct only when its start offset, end offset and label exactly match the gold annotation. This is stricter than token accuracy and is appropriate for redaction because a partially correct span may still leak sensitive text.

```text
precision = true positives / predicted entities
recall    = true positives / gold entities
F1        = 2 * precision * recall / (precision + recall)
```

### 5.2 Results

| Approach | Precision | Recall | Entity F1 | Token accuracy |
|---|---:|---:|---:|---:|
| Rules baseline | 1.0000 | 0.6255 | 0.7696 | N/A |
| Averaged perceptron | 0.9960 | 0.9960 | 0.9960 | 0.9992 |
| Hybrid rules + model | 0.9960 | 0.9960 | 0.9960 | N/A |

### 5.3 Interpretation

The rules baseline is precise but misses many PERSON and ORGANIZATION spans and some context-dependent addresses. Its recall of 0.6255 shows why deterministic patterns alone are not sufficient for natural financial language. The perceptron learns recurring context and token-shape patterns and recovers almost all gold spans. The hybrid system preserves the model’s high recall while applying explicit validation for card-like values.

The unusually high learned-model result is expected for a small, templated synthetic corpus and should not be interpreted as production-level generalization. A larger experiment would use held-out templates, naturally written text, noise, spelling variation, multilingual examples and human annotation.

## 6. Validation

The project includes five standard-library regression tests:

- Luhn validation accepts a test card number and rejects a bad checksum;
- the rule detector finds email, card and transaction entities;
- masking replaces values from right to left without offset corruption;
- the perceptron trains and produces a hybrid redaction;
- dataset offsets and BIO labels remain aligned.

Run:

```bash
python -m unittest discover -s tests -v
```

## 7. Limitations and ethical considerations

1. The corpus is synthetic and templated; it is not a substitute for a production benchmark.
2. The perceptron is intentionally small and is not a transformer model.
3. The API is a local educational service without authentication, rate limiting or persistence.
4. Redaction labels are not legal determinations of whether data is regulated.
5. Real values must never be copied into the demo corpus, prompts or committed files.
6. A production deployment needs access controls, key management, retention limits, monitoring, human review and a documented false-negative response.

## 8. Conclusion and future work

This project demonstrates a complete NER workflow from conceptual motivation to dataset construction, preprocessing, training, evaluation and an application API. The main contribution is the privacy-first hybrid architecture: contextual NER handles language variation while validators enforce high-confidence decisions for structured financial identifiers.

Future work should compare the perceptron with a pretrained transformer, add held-out template evaluation, introduce multilingual financial text, calibrate confidence scores, and integrate the detector with the SentinelOS compliance control plane. A production version would keep raw values inside a controlled scanner and send only masked spans and evidence metadata to downstream AI services.

## References

1. Lample, G., Ballesteros, M., Subramanian, S., Kawakami, K. and Dyer, C. (2016). *Neural Architectures for Named Entity Recognition*. NAACL-HLT.
2. Devlin, J., Chang, M.-W., Lee, K. and Toutanova, K. (2019). *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding*. NAACL-HLT.
3. Nadeau, D. and Sekine, S. (2007). *A survey of named entity recognition and classification*. Lingvisticae Investigationes.
4. Payment Card Industry Security Standards Council (2024). *PCI DSS v4.0.1*.
5. Luhn, H. P. (1960). *Computer for verifying numbers*. U.S. Patent 2,950,048.
