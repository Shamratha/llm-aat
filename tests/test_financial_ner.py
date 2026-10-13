from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.financial_ner.dataset import compose, generate_dataset, split_dataset
from src.financial_ner.pipeline import FinancialNERDetector
from src.financial_ner.perceptron import AveragedPerceptronNER
from src.financial_ner.rules import detect_rules, luhn_valid, mask_text


class FinancialNERTests(unittest.TestCase):
    def test_luhn_validation_accepts_test_card_and_rejects_bad_checksum(self) -> None:
        self.assertTrue(luhn_valid("4111 1111 1111 1111"))
        self.assertFalse(luhn_valid("4111 1111 1111 1112"))

    def test_rule_detector_finds_structured_pci_pii(self) -> None:
        text = "Email maya.rao@example.com, card 4111 1111 1111 1111, ref TXN-48291."
        labels = {entity.label for entity in detect_rules(text)}
        self.assertEqual(labels, {"EMAIL", "CARD_NUMBER", "TRANSACTION_ID"})

    def test_masking_replaces_from_right_to_left(self) -> None:
        text = "Email maya.rao@example.com and card 4111 1111 1111 1111."
        entities = detect_rules(text)
        masked = mask_text(text, entities)
        self.assertEqual(masked, "Email [EMAIL] and card [CARD_NUMBER].")
        self.assertNotIn("maya.rao@example.com", masked)

    def test_training_and_hybrid_prediction(self) -> None:
        examples = generate_dataset(72, seed=7)
        split = split_dataset(examples, seed=7)
        detector = FinancialNERDetector(AveragedPerceptronNER(epochs=3).fit(split.train))
        result = detector.redact("Maya Rao emailed maya.rao@example.com about TXN-48291.")
        self.assertIn("[EMAIL]", result["redacted_text"])
        self.assertTrue(result["entities"])

    def test_dataset_serializes_offsets_and_bio(self) -> None:
        example = compose([("Customer", None), ("Maya Rao", "PERSON"), ("emailed", None), ("maya.rao@example.com", "EMAIL")])
        self.assertEqual(len(example.tokens), len(example.bio_labels))
        self.assertIn("B-PERSON", example.bio_labels)
        self.assertIn("B-EMAIL", example.bio_labels)
        self.assertEqual(example.text[example.entities[0].start:example.entities[0].end], "Maya Rao")


if __name__ == "__main__":
    unittest.main()
