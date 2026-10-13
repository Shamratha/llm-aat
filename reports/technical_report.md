# Privacy-Preserving Named Entity Recognition for Automated PCI/PII Detection in Financial Text

**Course:** Natural Language Processing for LLM (24AM7PCLLM)
**Alternative Assessment Tool (AAT) Report**
**Department:** Machine Learning, B.M.S. College of Engineering
**Academic Year:** 2026–27, Session: July 2026–December 2026
**Semester & Section:** 7C
**Team details:** To be filled by the student members before submission.

## Abstract

Financial institutions process customer communications, payment events, support cases and operational logs that may contain personally identifiable information (PII) or payment-card information. Sending these texts directly to analytics systems or language models can create an avoidable privacy risk. This project implements a privacy-preserving Named Entity Recognition (NER) system that detects sensitive entities, validates structured payment identifiers, and returns redacted text with evidence metadata.

The project compares three approaches: a deterministic rules baseline, an averaged-perceptron contextual NER model trained on a synthetic financial corpus, and a hybrid detector that combines model predictions with validated rules. The corpus contains BIO annotations for PERSON, EMAIL, PHONE, CARD_NUMBER, ACCOUNT_NUMBER, TAX_ID, ADDRESS, TRANSACTION_ID and ORGANIZATION. Evaluation uses exact entity-level precision, recall and F1, together with token accuracy. On the reproducible 600-example test protocol, the rules baseline achieved an F1 of 0.7696, while both the averaged perceptron and hybrid system achieved an F1 of 0.9960. The result shows why context-aware learning is useful for unstructured entities and why deterministic checks remain important for structured financial identifiers.

## 1. Introduction

### 1.1 Background of Natural Language Processing

Natural Language Processing (NLP) is the area of Artificial Intelligence concerned with enabling computers to process, interpret and generate human language. NLP systems support information extraction, search, translation, summarization, question answering, conversational interfaces and compliance monitoring. Modern language-model systems are powerful, but their output quality and safety depend on the quality and privacy of the text given to them.

### 1.2 Importance of the Selected NLP Topic

Named Entity Recognition is important because it converts unstructured language into structured information. In financial services, the entities being extracted may be directly sensitive: a person’s name, email address, phone number, account identifier, tax identifier or payment-card number. Detecting those spans before a downstream model receives the text supports privacy-by-design and reduces accidental data exposure.

### 1.3 Objective of the Study

The objectives are to:

1. Study the NER task and its role in financial privacy operations.
2. Implement a synthetic, domain-specific NER corpus with BIO labels.
3. Compare deterministic rules, an interpretable learned model and a hybrid detector.
4. Validate structured card-like values using the Luhn checksum.
5. Provide a local API that returns redacted text and masked entity evidence.
6. Evaluate each approach using precision, recall, F1-score and token accuracy.

### 1.4 Scope of the Report

The report covers the conceptual review, real-world application, architecture, data generation, preprocessing, implementation, API behavior, evaluation, discussion, limitations and future work. The corpus is synthetic and the API is an educational local service. It is not a payment processor, a legal compliance certification or a production DLP system.

## 2. Selected NLP Topic Overview

### 2.1 Description of the NLP Task

NER assigns a semantic class to a text span. This implementation uses the BIO tagging scheme:

```text
Maya       B-PERSON
Rao        I-PERSON
emailed    O
maya...    B-EMAIL
```

The system detects PERSON, EMAIL, PHONE, CARD_NUMBER, ACCOUNT_NUMBER, TAX_ID, ADDRESS, TRANSACTION_ID and ORGANIZATION. Exact start and end character offsets are preserved because redaction must replace the complete sensitive value, not only part of it.

### 2.2 Real-World Use Cases

The same pattern can be used in:

- customer-support messages and call-centre transcripts;
- payment gateway and application logs;
- fraud-review notes and KYC case records;
- emails and incident reports;
- data exports sent to analysts or language-model applications;
- continuous PCI/PII compliance monitoring.

### 2.3 Relevance to the Syllabus and Industry

NER is a core sequence-labelling problem in NLP. The work applies the syllabus concept to a current industry problem: sensitive financial text must be classified before it is searched, summarized or passed to an LLM. It also demonstrates how classical methods, deterministic validators and an API can be combined into a usable application.

### 2.4 Key Challenges in This NLP Task

1. Structured identifiers require validation in addition to pattern matching.
2. Names and organizations are context-dependent and cannot be found reliably by simple regular expressions.
3. A false negative may leak sensitive data, while a false positive creates operational noise.
4. Exact span boundaries matter for safe redaction.
5. A classroom model may perform very well on templates but generalize poorly to naturally written text.

## 3. Real-Time Application / API Identified

### 3.1 Application or API Name

The application is the **Privacy-Preserving Financial NER API** included in this repository. It is a local JSON HTTP service implemented in `src/api.py`.

### 3.2 Purpose and Functionality

The API receives a financial-text message, detects sensitive entities and returns a redacted version. It also returns masked entity labels, offsets, detection source and a privacy note. A typical input is:

```text
Customer Maya Rao emailed maya.rao@example.com about card 4111 1111 1111 1111.
```

The output is:

```text
Customer [PERSON] emailed [EMAIL] about card [CARD_NUMBER].
```

### 3.3 Architecture or Platform on Which It Is Built

The service uses Python’s standard library and binds to `127.0.0.1`. It contains a tokenizer, rules module, averaged perceptron model, overlap resolver and redaction function. The design is dependency-free so the implementation can be reproduced on a normal academic laptop without downloading an external model or sending text to a third-party service.

### 3.4 Input/Output Behavior

| Endpoint | Input | Output |
|---|---|---|
| `GET /health` | None | Service status and model name |
| `GET /demo` | None | Standard synthetic redaction example |
| `POST /redact` | JSON text and method | Redacted text and masked entity metadata |

The POST body accepts `method` values `rules`, `model` or `hybrid`. The API rejects an empty text value or an unsupported method.

### 3.5 Limitations and Practical Considerations

The API has no authentication, persistence, rate limiting or production monitoring. It must not be given real customer or cardholder data without a security review. The implementation demonstrates the privacy boundary but does not itself establish that an organization is legally compliant.

## 4. NLP Model / Architecture Study

### 4.1 Theoretical Foundations of the Model

NER can be formulated as a sequence-labelling task. Given tokens \(x_1, x_2, ..., x_n\), the model predicts labels \(y_1, y_2, ..., y_n\). The labels describe whether a token is outside an entity, begins an entity or continues one. A learned model uses features of the current token and its context to select the most likely label.

### 4.2 Algorithm(s) Used

Three approaches are implemented:

1. **Rules baseline:** regular expressions for structured entities and Luhn validation for card-like values.
2. **Averaged perceptron:** an online linear classifier that predicts BIO labels from token and context features. Weights are averaged over training steps.
3. **Hybrid detector:** validated non-overlapping rule matches are retained, then non-overlapping model spans are added.

### 4.3 Architecture Diagram / Layer-Wise Design

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
                                     masked text + entities + evidence
```

### 4.4 Data Flow in the Model

The input sentence is tokenized without losing character positions. During training, gold entity spans are converted to BIO labels. The perceptron extracts word, shape, prefix, suffix, neighbour and previous-label features. During inference, rule and model outputs are merged. The final spans are passed to a right-to-left masking function so earlier character offsets remain valid.

### 4.5 Mathematical Formulation

For a candidate label \(y\) and feature vector \(f(x_i, y)\), the perceptron score is:

\[
S(y \mid x_i) = \mathbf{w}_y \cdot f(x_i, y)
\]

The predicted label is the label with the greatest score. If the prediction differs from the gold label, the gold feature weights are increased and the predicted feature weights are decreased. Averaging is applied across update steps before inference.

### 4.6 Why This Model Suits the Selected NLP Task

The perceptron is interpretable, quick to train and sufficient to demonstrate sequence labelling. It learns contextual entities that regular expressions cannot identify. Rules remain valuable for payment-card data because a deterministic Luhn check makes the decision auditable. This combination reflects a practical financial-data protection architecture rather than treating all entities as ordinary text.

## 5. Dataset and Preprocessing

### 5.1 Dataset Description

The corpus is generated deterministically by `src/financial_ner/dataset.py`. It contains 600 synthetic examples from payment support, KYC, refunds, billing addresses, transaction reviews, privacy assessments and operational escalations. The generated JSONL records contain the source sentence, character-level spans, token offsets and BIO labels.

### 5.2 Data Cleaning Steps

The generator uses reserved example domains and synthetic identifiers. Entity spans are created before tokenization, and all values are checked for valid offsets. No real personal, account or payment-card information is used. The generated records are shuffled with seed `42` to make the experiment repeatable.

### 5.3 Tokenization, Lemmatization, Stopwords Removal

The project uses a lightweight regular-expression tokenizer because punctuation and identifier separators are important for financial entities. Lemmatization and stopword removal are intentionally not applied: removing words such as `card`, `account` or `transaction` would remove useful context, and changing token text could break exact character offsets needed for redaction.

### 5.4 Train/Test Split Strategy

The split is 70% training, 15% development and 15% test:

| Split | Examples |
|---|---:|
| Train | 420 |
| Development | 90 |
| Test | 90 |

The test set is not used to update weights. The current report uses the fixed eight-epoch setup and seed `42`.

### 5.5 Feature Engineering or Embedding Approach

The model uses sparse, interpretable features rather than pretrained embeddings:

- lower-cased token;
- token shape, such as `Xx-dd`;
- two-character prefix and suffix;
- previous and next two tokens;
- three-token context;
- digit, uppercase and title-case flags;
- previous predicted BIO label.

## 6. Implementation Methodology

### 6.1 Tools, Libraries, and Environment Used

The implementation uses Python 3.10+ and the Python standard library. No external runtime dependencies are required. The project uses `unittest`, `json`, `csv`, `re`, `http.server`, `zipfile` and `dataclasses`. The generated DOCX and PPTX files are packaged as valid Office Open XML archives by `tools/build_artifacts.py`.

### 6.2 Model Implementation Steps

1. Generate synthetic examples and gold entity spans.
2. Tokenize while preserving character offsets.
3. Convert spans into BIO labels.
4. Train the averaged perceptron on 420 examples for eight epochs.
5. Run the rules baseline, learned model and hybrid detector on the 90-example test split.
6. Calculate exact entity-level metrics and token accuracy.
7. Save `metrics.json`, `metrics.csv`, `sample_predictions.json` and `dataset.jsonl`.

### 6.3 API Integration

Run the service with:

```bash
python -m src.api
```

Then send a JSON request to `http://127.0.0.1:8080/redact`. The service trains a smaller 240-example demo model at startup to keep local startup quick; the reported experiment remains the full 600-example protocol.

### 6.4 Pseudocode / Workflow Diagram

```text
train_detector(seed):
    examples = generate_dataset(600, seed)
    train, dev, test = split(examples)
    model = averaged_perceptron.fit(train)
    for example in test:
        rules = detect_rules(example.text)
        learned = model.predict(example.text)
        hybrid = merge_non_overlapping(rules, learned)
    return metrics

redact(text):
    entities = hybrid_detector(text)
    return replace_spans_right_to_left(text, entities)
```

### 6.5 Hyperparameters and Training Configuration

| Parameter | Value |
|---|---:|
| Dataset size | 600 |
| Train/dev/test | 70% / 15% / 15% |
| Random seed | 42 |
| Perceptron epochs | 8 |
| Evaluation | Exact entity span and label match |
| API demo corpus | 240 examples |

## 7. Results and Evaluation

### 7.1 Performance Metrics

An entity is correct only when its start offset, end offset and label exactly match the gold annotation. This is stricter than token accuracy and is appropriate for redaction because a partially correct span may still leak sensitive text.

\[
Precision = TP / Predicted, \quad Recall = TP / Actual
\]

\[
F1 = 2 \times Precision \times Recall / (Precision + Recall)
\]

### 7.2 Visualization of Results

The generated `outputs/metrics.csv` can be plotted as a grouped bar chart for precision, recall and F1. The numerical comparison is:

| Approach | Precision | Recall | Entity F1 | Token Accuracy |
|---|---:|---:|---:|---:|
| Rules baseline | 1.0000 | 0.6255 | 0.7696 | N/A |
| Averaged perceptron | 0.9960 | 0.9960 | 0.9960 | 0.9992 |
| Hybrid rules + model | 0.9960 | 0.9960 | 0.9960 | N/A |

### 7.3 Qualitative and Quantitative Analysis

The rules baseline is precise but misses many PERSON and ORGANIZATION spans and some context-dependent addresses. The learned model recovers contextual entities and achieves almost complete span coverage on the templated test set. The hybrid detector retains validated structured matches while using the model for language-dependent entities.

### 7.4 Error Analysis

The main baseline errors are false negatives for names and organizations, which do not have a reliable surface pattern. Address spans are also difficult when a sentence uses a different cue or punctuation. The learned model’s remaining error comes from a single context-dependent address/person boundary in the reported split. The high score is expected for a small, templated corpus and should not be interpreted as production generalization.

### 7.5 Comparison Between Approaches

The comparison supports a clear design decision. A rules-only system is transparent but incomplete. A learned model improves contextual recall. A hybrid system provides a practical compromise because it keeps structured financial validation explicit while adding language understanding.

## 8. Discussion

### 8.1 Interpretation of Results

The results show that NER is not only a text-analytics task; it can act as a privacy gateway. The rules baseline’s recall of 0.6255 demonstrates that pattern matching alone will miss sensitive entities in ordinary language. Contextual learning increases coverage, while deterministic validation protects high-risk identifiers.

### 8.2 Strengths and Weaknesses of the Model

**Strengths:** interpretable features, fast training, deterministic card validation, exact offsets, no external services and a usable local API.
**Weaknesses:** synthetic templates, no pretrained language representation, no authentication, no multilingual support and limited generalization evidence.

### 8.3 Challenges Encountered During Implementation

The key implementation challenges were preserving span offsets through tokenization, preventing overlap between rule and model results, validating card-like values without leaking them, and keeping the experiment dependency-free. The evaluation also needed exact entity matching rather than only token-level accuracy.

### 8.4 Impact of Dataset Quality and Preprocessing

The corpus makes the workflow reproducible but is not naturally distributed language. Repeated templates make learning easier and explain the high F1 result. Preserving punctuation and context words is more useful than stopword removal because terms such as `card`, `account` and `transaction` help distinguish entity types.

### 8.5 How the API or Application Enhances the NLP Task

The API converts an academic model into an observable application. It demonstrates a realistic input/output contract, exposes method comparisons, returns evidence metadata and performs redaction before downstream processing. This makes the NER result actionable for privacy operations rather than leaving it as a notebook prediction.

## 9. Conclusion

### 9.1 Summary of the Work Done

This AAT implemented a complete financial NER workflow: conceptual review, synthetic corpus generation, preprocessing, rules baseline, averaged perceptron training, hybrid inference, exact-span evaluation and a local redaction API.

### 9.2 Key Learnings and Insights

The main learning is that financial privacy detection benefits from combining NLP and deterministic checks. Contextual models are useful for names and organizations, while rules and Luhn validation make decisions about structured payment identifiers explainable.

### 9.3 Real-World Applicability

The design can be placed before an LLM, support platform, data warehouse, log pipeline or audit workflow. A production deployment would keep raw values inside a controlled scanner and expose only masked spans and evidence metadata to downstream services.

### 9.4 Future Improvements or Extensions

Future work should use held-out templates, human-labelled naturally written text, multilingual data, calibrated confidence, a pretrained transformer comparison, stronger access control and integration with the SentinelOS compliance control plane.

## 10. References

1. Lample, G., Ballesteros, M., Subramanian, S., Kawakami, K. and Dyer, C. (2016). *Neural Architectures for Named Entity Recognition*. NAACL-HLT.
2. Devlin, J., Chang, M.-W., Lee, K. and Toutanova, K. (2019). *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding*. NAACL-HLT.
3. Nadeau, D. and Sekine, S. (2007). *A survey of named entity recognition and classification*. Lingvisticae Investigationes.
4. Payment Card Industry Security Standards Council (2024). *PCI DSS v4.0.1*.
5. Luhn, H. P. (1960). *Computer for verifying numbers*. U.S. Patent 2,950,048.
