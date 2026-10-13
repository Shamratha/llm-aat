from __future__ import annotations

import argparse
import json

from .financial_ner.pipeline import run_pipeline, train_detector


DEMO_TEXT = "Maya Rao emailed maya.rao@example.com about card 4111 1111 1111 1111 for transaction TXN-48291."


def main() -> None:
    parser = argparse.ArgumentParser(description="Privacy-preserving financial NER")
    subparsers = parser.add_subparsers(dest="command", required=True)
    pipeline_parser = subparsers.add_parser("pipeline", help="Generate data, train models and evaluate")
    pipeline_parser.add_argument("--seed", type=int, default=42)
    pipeline_parser.add_argument("--size", type=int, default=600)
    demo_parser = subparsers.add_parser("demo", help="Run a local redaction example")
    demo_parser.add_argument("--text", default=DEMO_TEXT)
    args = parser.parse_args()

    if args.command == "pipeline":
        metrics = run_pipeline(args.seed, args.size)
        print(json.dumps({
            "dataset": metrics["splits"],
            "results": [
                {"approach": result["name"], "precision": result["entity"]["micro"]["precision"], "recall": result["entity"]["micro"]["recall"], "f1": result["entity"]["micro"]["f1"]}
                for result in metrics["results"]
            ],
        }, indent=2))
    else:
        detector = train_detector()
        print(json.dumps(detector.redact(args.text), indent=2))


if __name__ == "__main__":
    main()
