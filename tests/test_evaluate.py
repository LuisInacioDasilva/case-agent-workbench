import json
import unittest
from pathlib import Path

from app.evaluate import evaluate
from app.providers import DemoProvider
from app.workflow import Workbench


class EvaluationTests(unittest.TestCase):
    def test_regression_corpus_passes_without_external_model(self):
        cases = json.loads((Path(__file__).parents[1] / "data" / "evals.json").read_text(encoding="utf-8"))
        report = evaluate(Workbench(provider=DemoProvider()), cases)
        self.assertEqual(report["passed"], len(cases))
        self.assertEqual(report["pass_rate"], 1.0)
        self.assertNotIn("case", report["results"][0])

    def test_failure_is_visible_per_check(self):
        report = evaluate(Workbench(), [{
            "case": "O áudio do cliente não reproduz no WhatsApp.",
            "expected_category": "order",
            "expected_citation": "KB-ORDER-02",
        }])
        self.assertEqual(report["passed"], 0)
        self.assertFalse(report["results"][0]["checks"]["category"])
        self.assertFalse(report["results"][0]["checks"]["citation"])

    def test_empty_corpus_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(Workbench(), [])


if __name__ == "__main__":
    unittest.main()
