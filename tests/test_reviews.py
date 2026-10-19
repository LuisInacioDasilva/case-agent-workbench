import unittest
from unittest.mock import patch

from app.reviews import ReviewNotFound, ReviewQueue


def analysis():
    return {
        "status": "review_required",
        "draft": {"category": "audio", "answer": "Verificar codec e confirmação.", "citations": ["KB-AUDIO-01"]},
        "evidence": [{"id": "KB-AUDIO-01", "title": "Entrega de áudio"}],
        "case": "Este texto original não deve ser persistido.",
    }


class ReviewQueueTests(unittest.TestCase):
    def test_decision_is_single_use_and_never_keeps_original_case(self):
        queue = ReviewQueue()
        ticket = queue.submit(analysis())
        self.assertNotIn("case", queue.items[ticket["id"]])
        self.assertEqual(len(queue.pending()), 1)
        decided = queue.decide(ticket["id"], "approve", "Luis", "Fontes conferidas")
        self.assertEqual(decided["status"], "approved_for_display")
        self.assertEqual(queue.pending(), [])
        with self.assertRaises(RuntimeError):
            queue.decide(ticket["id"], "reject", "Luis", "Mudança de ideia")

    def test_queue_is_bounded_and_expires(self):
        full = ReviewQueue(capacity=1)
        full.submit(analysis())
        with self.assertRaises(OverflowError):
            full.submit(analysis())

        with patch("app.reviews.monotonic", side_effect=[100, 100, 100, 102, 102, 102]):
            queue = ReviewQueue(capacity=1, ttl_seconds=1)
            first = queue.submit(analysis())
            self.assertEqual(len(queue.pending()), 1)
            second = queue.submit(analysis())
            self.assertNotEqual(first["id"], second["id"])

    def test_missing_or_invalid_decision_is_rejected(self):
        queue = ReviewQueue()
        ticket = queue.submit(analysis())
        with self.assertRaises(ValueError):
            queue.decide(ticket["id"], "approve", "L", "curto")
        with self.assertRaises(ReviewNotFound):
            queue.decide("00000000-0000-0000-0000-000000000000", "reject", "Luis", "Sem fonte")


if __name__ == "__main__":
    unittest.main()
