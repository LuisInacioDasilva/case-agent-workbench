"""Repeatable evaluation of the local agent workflow; never writes input cases."""

import argparse
import json
from pathlib import Path

from .providers import DemoProvider, OllamaProvider
from .workflow import Workbench

DEFAULT_CASES = Path(__file__).resolve().parents[1] / "data" / "evals.json"


def evaluate(workbench: Workbench, cases: list[dict]) -> dict:
    if not cases:
        raise ValueError("evaluation corpus cannot be empty")
    results = []
    for index, item in enumerate(cases, start=1):
        result = workbench.analyze(item["case"])
        draft = result.get("draft", {})
        checks = {
            "status": result["status"] == item.get("expected_status", "review_required"),
            "category": draft.get("category") == item["expected_category"],
            "citation": item["expected_citation"] in draft.get("citations", []),
            "human_review": draft.get("needs_human") is True,
        }
        results.append({"case_number": index, "passed": all(checks.values()), "checks": checks})
    passed = sum(row["passed"] for row in results)
    return {
        "mode": workbench.provider.model,
        "total": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 4),
        "results": results,
        "note": "Métrica deste corpus sintético; não mede precisão em produção.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Avaliar os controles do Case Agent Workbench")
    parser.add_argument("--mode", choices=("demo", "ollama"), default="demo")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=Path("dist/evaluation.json"))
    args = parser.parse_args()
    corpus = json.loads(args.cases.read_text(encoding="utf-8"))
    provider = OllamaProvider() if args.mode == "ollama" else DemoProvider()
    report = evaluate(Workbench(provider=provider), corpus)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['passed']}/{report['total']} casos passaram; relatório: {args.output}")
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
