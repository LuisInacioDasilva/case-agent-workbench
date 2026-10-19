import json
import re
import unicodedata
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge.json"


def tokens(value: str) -> set[str]:
    plain = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(ch for ch in plain if not unicodedata.combining(ch))
    return {word for word in re.findall(r"[a-z0-9]+", plain) if len(word) > 2}


class KnowledgeBase:
    def __init__(self, path: Path = DATA_PATH):
        self.documents = json.loads(path.read_text(encoding="utf-8"))
        ids = [doc["id"] for doc in self.documents]
        if len(ids) != len(set(ids)):
            raise ValueError("knowledge IDs must be unique")

    def search(self, query: str, limit: int = 2) -> list[dict]:
        query_terms = tokens(query)
        ranked = sorted(
            self.documents,
            key=lambda doc: (
                len(query_terms & tokens(doc["title"] + " " + doc["text"])),
                doc["id"],
            ),
            reverse=True,
        )
        positive = [doc for doc in ranked if query_terms & tokens(doc["title"] + " " + doc["text"])]
        general = next(doc for doc in self.documents if doc["id"] == "KB-GENERAL-04")
        selected = positive[:limit]
        if not selected:
            selected = [general]
        return selected
