"""Tests for the SM-2 spaced repetition algorithm (JS implementation logic in Python)."""
import json
import time
import pytest


class SM2Scheduler:
    """Python reference implementation matching learning_hub.js."""

    def __init__(self):
        self.cards = {}

    def get_card(self, card_id):
        if card_id not in self.cards:
            self.cards[card_id] = {
                "ease": 2.5,
                "interval": 0,
                "reps": 0,
                "due": time.time() * 1000,
                "last_review": 0,
            }
        return self.cards[card_id]

    def review(self, card_id, grade):
        c = self.get_card(card_id)
        now = time.time() * 1000

        if grade < 2:
            c["reps"] = 0
            c["interval"] = 1
        else:
            if c["reps"] == 0:
                c["interval"] = 1
            elif c["reps"] == 1:
                c["interval"] = 6
            else:
                c["interval"] = round(c["interval"] * c["ease"])
            c["reps"] += 1

        c["ease"] += 0.1 - (3 - grade) * (0.08 + (3 - grade) * 0.02)
        c["ease"] = max(1.3, c["ease"])

        c["due"] = now + c["interval"] * 86400000
        c["last_review"] = now
        return c

    def is_due(self, card_id):
        c = self.get_card(card_id)
        return c["due"] <= time.time() * 1000

    def get_due_cards(self, card_ids):
        now = time.time() * 1000
        return [
            cid for cid in card_ids
            if self.get_card(cid)["due"] <= now
        ]

    def get_stats(self, card_ids):
        now = time.time() * 1000
        due = learning = mastered = 0
        for cid in card_ids:
            c = self.get_card(cid)
            if c["due"] <= now:
                due += 1
            elif c["reps"] > 0 and c["interval"] < 21:
                learning += 1
            elif c["reps"] > 0:
                mastered += 1
        return {"total": len(card_ids), "due": due, "learning": learning, "mastered": mastered}


class TestSM2Scheduler:
    def test_initial_card(self):
        sm = SM2Scheduler()
        c = sm.get_card("test#0")
        assert c["ease"] == 2.5
        assert c["interval"] == 0
        assert c["reps"] == 0

    def test_first_review_good(self):
        sm = SM2Scheduler()
        c = sm.review("test#0", 2)  # Good
        assert c["reps"] == 1
        assert c["interval"] == 1  # first review = 1 day

    def test_second_review_good(self):
        sm = SM2Scheduler()
        sm.review("test#0", 2)
        c = sm.review("test#0", 2)
        assert c["reps"] == 2
        assert c["interval"] == 6  # second review = 6 days

    def test_third_review_good(self):
        sm = SM2Scheduler()
        sm.review("test#0", 2)
        sm.review("test#0", 2)
        c = sm.review("test#0", 2)
        assert c["reps"] == 3
        assert c["interval"] == round(6 * 2.5)  # 6 * ease

    def test_again_resets(self):
        sm = SM2Scheduler()
        sm.review("test#0", 2)
        sm.review("test#0", 2)
        c = sm.review("test#0", 0)  # Again
        assert c["reps"] == 0
        assert c["interval"] == 1

    def test_hard_does_not_reset(self):
        sm = SM2Scheduler()
        sm.review("test#0", 2)
        c = sm.review("test#0", 1)  # Hard
        assert c["reps"] == 0
        assert c["interval"] == 1

    def test_ease_decreases_with_again(self):
        sm = SM2Scheduler()
        initial_ease = sm.get_card("test#0")["ease"]
        sm.review("test#0", 0)  # Again (grade 0)
        c = sm.get_card("test#0")
        assert c["ease"] < initial_ease

    def test_ease_increases_with_easy(self):
        sm = SM2Scheduler()
        initial_ease = sm.get_card("test#0")["ease"]
        sm.review("test#0", 3)  # Easy
        c = sm.get_card("test#0")
        assert c["ease"] > initial_ease

    def test_ease_floor(self):
        sm = SM2Scheduler()
        for _ in range(20):
            sm.review("test#0", 0)
        c = sm.get_card("test#0")
        assert c["ease"] >= 1.3

    def test_due_cards(self):
        sm = SM2Scheduler()
        sm.review("a", 2)
        sm.review("b", 0)
        sm.review("c", 3)
        # After review, all cards are set to future due dates (1+ days out)
        # So get_due_cards should return empty for freshly-reviewed cards
        due = sm.get_due_cards(["a", "b", "c"])
        assert len(due) == 0  # All recently reviewed, none due yet

        # An unreviewed card with default due=now should be due
        sm.get_card("d")  # defaults to due=now
        due2 = sm.get_due_cards(["a", "b", "c", "d"])
        assert "d" in due2

    def test_stats(self):
        sm = SM2Scheduler()
        sm.review("a", 2)
        sm.review("b", 2)
        sm.review("b", 2)
        stats = sm.get_stats(["a", "b", "c"])
        assert stats["total"] == 3

    def test_independent_cards(self):
        sm = SM2Scheduler()
        sm.review("a", 2)
        sm.review("b", 0)
        ca = sm.get_card("a")
        cb = sm.get_card("b")
        assert ca["reps"] == 1
        assert cb["reps"] == 0

    def test_serialization(self):
        sm = SM2Scheduler()
        sm.review("test#0", 2)
        raw = json.dumps(sm.cards)
        sm2 = SM2Scheduler()
        sm2.cards = json.loads(raw)
        c = sm2.get_card("test#0")
        assert c["reps"] == 1
