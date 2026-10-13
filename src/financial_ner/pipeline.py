from __future__ import annotations

import csv
import json
from pathlib import Path

from .dataset import generate_dataset, split_dataset, write_jsonl
from .metrics import evaluate
from .perceptron import AveragedPerceptronNER
from .rules import detect_rules, mask_text, merge_entities
from .types import Entity, Example


class FinancialNERDetector:
    def __init__(self, model: AveragedPerceptronNER) -> None:
        self.model = model

    def detect(self, text: str, method: str = "hybrid") -> list[Entity]:
        model_entities = self.model.predict_entities(text)
        rule_entities = detect_rules(text)
        if method == "rules":
            return rule_entities
        if method == "model":
            return model_entities
        return merge_entities(text, model_entities, rule_entities)

    def redact(self, text: str, method: str = "hybrid") -> dict:
        entities = self.detect(text, method)
        return {
            "text": text,
            "redacted_text": mask_text(text, entities),
            "entities": [entity.to_dict(masked=True) for entity in entities],
            "method": method,
            "privacy_note": "Only masked entity metadata should be forwarded to downstream language models.",
        }


def train_detector(seed: int = 42, size: int = 600) -> FinancialNERDetector:
    examples = generate_dataset(size, seed)
    split = split_dataset(examples, seed)
    return FinancialNERDetector(AveragedPerceptronNER(epochs=8).fit(split.train))


def _write_metrics_csv(results: list[dict], destination: Path) -> None:
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["approach", "entity_precision", "entity_recall", "entity_f1", "token_accuracy"])
        for result in results:
            micro = result["entity"]["micro"]
            writer.writerow([
                result["name"],
                micro["precision"],
                micro["recall"],
                micro["f1"],
                result.get("token", {}).get("accuracy", "n/a"),
            ])


def run_pipeline(seed: int = 42, size: int = 600, output_dir: str | Path = "outputs") -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    examples = generate_dataset(size, seed)
    split = split_dataset(examples, seed)
    write_jsonl(examples, output / "dataset.jsonl")

    model = AveragedPerceptronNER(epochs=8).fit(split.train)
    detector = FinancialNERDetector(model)
    rule_predictions = [detect_rules(example.text) for example in split.test]
    model_predictions = [model.predict_entities(example.text) for example in split.test]
    hybrid_predictions = [merge_entities(example.text, model_entities, detect_rules(example.text)) for example, model_entities in zip(split.test, model_predictions)]
    model_token_predictions = [model.predict_labels(example.text) for example in split.test]

    results = [
        evaluate("Rules baseline", split.test, rule_predictions),
        evaluate("Averaged perceptron", split.test, model_predictions, model_token_predictions),
        evaluate("Hybrid rules + model", split.test, hybrid_predictions),
    ]
    metrics = {
        "project": "Privacy-Preserving Financial NER",
        "seed": seed,
        "dataset_size": size,
        "splits": {"train": len(split.train), "dev": len(split.dev), "test": len(split.test)},
        "entity_types": ["PERSON", "EMAIL", "PHONE", "CARD_NUMBER", "ACCOUNT_NUMBER", "TAX_ID", "ADDRESS", "TRANSACTION_ID", "ORGANIZATION"],
        "results": results,
        "interpretation": "The hybrid detector keeps validated structured matches from rules and fills contextual gaps with the learned model.",
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _write_metrics_csv(results, output / "metrics.csv")

    samples = []
    for example in split.test[:8]:
        samples.append({
            "input": example.text,
            "gold_entities": [entity.to_dict(masked=True) for entity in example.entities],
            "hybrid_output": detector.redact(example.text),
        })
    (output / "sample_predictions.json").write_text(json.dumps(samples, indent=2), encoding="utf-8")
    return metrics
