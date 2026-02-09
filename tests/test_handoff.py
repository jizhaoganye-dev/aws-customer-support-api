"""
Unit tests for handoff module.
Tests context extraction, priority determination, and summary generation.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'layers', 'common', 'python'))

from handoff import build_handoff_context


class TestHandoffContext:
    """Test AI-to-Human handoff context builder."""

    def _make_messages(self, texts: list[tuple[str, str]]) -> list[dict]:
        """Helper to create message dicts."""
        return [{"role": role, "content": content} for role, content in texts]

    # ── Order number extraction ───────────────────────────────────────────

    def test_extract_order_number(self):
        messages = self._make_messages([
            ("user", "注文番号 ORD-12345 の商品が届きません"),
        ])
        ctx = build_handoff_context("conv-1", messages)
        assert "ORD-12345" in ctx.order_numbers

    def test_multiple_order_numbers(self):
        messages = self._make_messages([
            ("user", "注文番号 ORD-001 と order#ORD-002 について"),
        ])
        ctx = build_handoff_context("conv-1", messages)
        assert len(ctx.order_numbers) >= 1

    # ── Issue extraction ──────────────────────────────────────────────────

    def test_detect_shipping_issue(self):
        messages = self._make_messages([
            ("user", "商品が届かないんですが"),
        ])
        ctx = build_handoff_context("conv-1", messages)
        assert "配送問題" in ctx.detected_issues

    def test_detect_quality_issue(self):
        messages = self._make_messages([
            ("user", "届いた商品が壊れています"),
        ])
        ctx = build_handoff_context("conv-1", messages)
        assert "品質問題" in ctx.detected_issues

    def test_detect_return_issue(self):
        messages = self._make_messages([
            ("user", "返品したいのですが"),
        ])
        ctx = build_handoff_context("conv-1", messages)
        assert "返品・返金" in ctx.detected_issues

    def test_detect_billing_issue(self):
        messages = self._make_messages([
            ("user", "請求がおかしいです。二重課金されています。"),
        ])
        ctx = build_handoff_context("conv-1", messages)
        assert "料金問題" in ctx.detected_issues

    # ── Priority determination ────────────────────────────────────────────

    def test_critical_priority_for_critical_harassment(self):
        messages = self._make_messages([("user", "対応しろ")])
        ctx = build_handoff_context(
            "conv-1", messages,
            harassment_detected=True,
            harassment_severity="critical",
        )
        assert ctx.priority == "critical"

    def test_high_priority_for_anger(self):
        messages = self._make_messages([("user", "怒ってる")])
        ctx = build_handoff_context(
            "conv-1", messages,
            sentiment_history=["anger", "anger"],
        )
        assert ctx.priority == "high"

    def test_normal_priority_for_calm_conversation(self):
        messages = self._make_messages([
            ("user", "注文状況を確認したいです"),
        ])
        ctx = build_handoff_context("conv-1", messages)
        assert ctx.priority == "normal"

    # ── Summary generation ────────────────────────────────────────────────

    def test_summary_contains_message_count(self):
        messages = self._make_messages([
            ("user", "こんにちは"),
            ("assistant", "いらっしゃいませ"),
            ("user", "商品について聞きたい"),
        ])
        ctx = build_handoff_context("conv-1", messages)
        assert "2" in ctx.summary  # 2 customer messages

    def test_summary_contains_first_message(self):
        messages = self._make_messages([
            ("user", "商品が壊れています"),
        ])
        ctx = build_handoff_context("conv-1", messages)
        assert "壊れ" in ctx.summary

    # ── Metadata ──────────────────────────────────────────────────────────

    def test_metadata_contains_timestamp(self):
        messages = self._make_messages([("user", "test")])
        ctx = build_handoff_context("conv-1", messages)
        assert "handoff_timestamp" in ctx.metadata

    def test_metadata_message_counts(self):
        messages = self._make_messages([
            ("user", "msg1"),
            ("assistant", "reply1"),
            ("user", "msg2"),
        ])
        ctx = build_handoff_context("conv-1", messages)
        assert ctx.metadata["total_messages"] == 3
        assert ctx.metadata["customer_messages"] == 2

    # ── Serialization ─────────────────────────────────────────────────────

    def test_to_dict(self):
        messages = self._make_messages([("user", "test")])
        ctx = build_handoff_context("conv-1", messages, customer_name="テスト太郎")
        d = ctx.to_dict()
        assert d["conversation_id"] == "conv-1"
        assert d["customer_name"] == "テスト太郎"
        assert isinstance(d["metadata"], dict)
