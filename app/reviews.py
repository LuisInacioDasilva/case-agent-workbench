"""Local, bounded human-review queue. Never stores the original case text."""

from collections import OrderedDict
from copy import deepcopy
from threading import RLock
from time import monotonic
from uuid import uuid4


class ReviewNotFound(LookupError):
    pass


class ReviewQueue:
    def __init__(self, capacity: int = 100, ttl_seconds: int = 3600):
        if capacity < 1 or ttl_seconds < 1:
            raise ValueError("capacity and TTL must be positive")
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self.items = OrderedDict()
        self.lock = RLock()

    def _expire(self):
        now = monotonic()
        for key in list(self.items):
            if self.items[key]["expires_at"] <= now:
                del self.items[key]

    def submit(self, analysis: dict) -> dict:
        if analysis.get("status") != "review_required":
            raise ValueError("only reviewed drafts can enter the queue")
        with self.lock:
            self._expire()
            if len(self.items) >= self.capacity:
                raise OverflowError("review queue is full")
            ticket = {
                "id": str(uuid4()),
                "status": "pending",
                "draft": deepcopy(analysis["draft"]),
                "evidence": deepcopy(analysis["evidence"]),
                "decision": None,
                "actor": None,
                "reason": None,
                "expires_at": monotonic() + self.ttl_seconds,
            }
            self.items[ticket["id"]] = ticket
            return self._public(ticket)

    def pending(self) -> list[dict]:
        with self.lock:
            self._expire()
            return [self._public(item) for item in self.items.values() if item["status"] == "pending"]

    def decide(self, ticket_id: str, decision: str, actor: str, reason: str) -> dict:
        if decision not in {"approve", "reject"}:
            raise ValueError("decision must be approve or reject")
        if not isinstance(actor, str) or not 2 <= len(actor.strip()) <= 80:
            raise ValueError("actor must have 2 to 80 characters")
        if not isinstance(reason, str) or not 5 <= len(reason.strip()) <= 300:
            raise ValueError("reason must have 5 to 300 characters")
        with self.lock:
            self._expire()
            item = self.items.get(ticket_id)
            if item is None:
                raise ReviewNotFound("review not found or expired")
            if item["status"] != "pending":
                raise RuntimeError("review already decided")
            item["status"] = "approved_for_display" if decision == "approve" else "rejected"
            item["decision"] = decision
            item["actor"] = actor.strip()
            item["reason"] = reason.strip()
            return self._public(item)

    @staticmethod
    def _public(item: dict) -> dict:
        return {key: deepcopy(item[key]) for key in (
            "id", "status", "draft", "evidence", "decision", "actor", "reason"
        )}
