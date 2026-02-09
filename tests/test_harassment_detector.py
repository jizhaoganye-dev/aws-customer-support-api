"""
Unit tests for harassment_detector module.
Tests pattern matching, severity classification, and edge cases.
"""
import sys
import os
import pytest

# Add layer to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'layers', 'common', 'python'))

from harassment_detector import detect_harassment, Severity


class TestHarassmentDetector:
    """Test harassment detection patterns and severity classification."""

    # ── Critical severity tests ───────────────────────────────────────────

    def test_death_threat_detected(self):
        result = detect_harassment("お前を殺すぞ")
        assert result.is_harassment is True
        assert result.severity == Severity.CRITICAL

    def test_death_wish_detected(self):
        result = detect_harassment("死ね")
        assert result.is_harassment is True
        assert result.severity == Severity.CRITICAL

    def test_violence_threat(self):
        result = detect_harassment("会社を爆破してやる")
        assert result.is_harassment is True
        assert result.severity == Severity.CRITICAL

    def test_legal_threat(self):
        result = detect_harassment("訴えてやるからな")
        assert result.is_harassment is True
        assert result.severity == Severity.CRITICAL

    # ── High severity tests ───────────────────────────────────────────────

    def test_insult_baka(self):
        result = detect_harassment("このバカ野郎")
        assert result.is_harassment is True
        assert result.severity == Severity.HIGH

    def test_insult_aho(self):
        result = detect_harassment("アホかお前")
        assert result.is_harassment is True
        assert result.severity == Severity.HIGH

    def test_insult_kasu(self):
        result = detect_harassment("クズみたいな対応だな")
        assert result.is_harassment is True
        assert result.severity == Severity.HIGH

    def test_insult_gomi(self):
        result = detect_harassment("ゴミみたいなサービス")
        assert result.is_harassment is True
        assert result.severity == Severity.HIGH

    def test_contempt(self):
        result = detect_harassment("ふざけるなよ！")
        assert result.is_harassment is True
        assert result.severity == Severity.HIGH

    def test_incompetence_insult(self):
        result = detect_harassment("お前は無能だな")
        assert result.is_harassment is True
        assert result.severity == Severity.HIGH

    # ── Medium severity tests ─────────────────────────────────────────────

    def test_urgency_pressure(self):
        result = detect_harassment("今すぐ対応しろ")
        assert result.is_harassment is True
        assert result.severity == Severity.MEDIUM

    def test_escalation_demand(self):
        result = detect_harassment("責任者を出せ")
        assert result.is_harassment is True
        assert result.severity == Severity.MEDIUM

    def test_social_media_threat(self):
        result = detect_harassment("Twitterで晒すからな")
        assert result.is_harassment is True
        assert result.severity == Severity.MEDIUM

    def test_compensation_demand(self):
        result = detect_harassment("金を返せ！弁償しろ！")
        assert result.is_harassment is True
        assert result.severity == Severity.MEDIUM

    # ── Low severity / No harassment tests ────────────────────────────────

    def test_mild_frustration(self):
        result = detect_harassment("すごく困っているんです")
        assert result.severity == Severity.LOW

    def test_normal_complaint(self):
        result = detect_harassment("商品が遅いです")
        assert result.severity == Severity.LOW

    def test_polite_message(self):
        result = detect_harassment("注文番号を教えてください")
        assert result.is_harassment is False
        assert result.severity == Severity.NONE

    def test_empty_message(self):
        result = detect_harassment("")
        assert result.is_harassment is False
        assert result.severity == Severity.NONE

    def test_none_input(self):
        result = detect_harassment(None)
        assert result.is_harassment is False

    # ── Confidence tests ──────────────────────────────────────────────────

    def test_single_match_confidence(self):
        result = detect_harassment("バカ")
        assert 0.6 <= result.confidence <= 0.8

    def test_multiple_match_confidence(self):
        result = detect_harassment("バカ！クズ！ゴミ！死ね！殺すぞ！")
        assert result.confidence >= 0.9

    # ── Result serialization ──────────────────────────────────────────────

    def test_to_dict(self):
        result = detect_harassment("バカ野郎")
        d = result.to_dict()
        assert "is_harassment" in d
        assert "severity" in d
        assert "confidence" in d
        assert "matched_patterns" in d
        assert "categories" in d
        assert "recommendation" in d
        assert isinstance(d["severity"], str)


class TestHarassmentEdgeCases:
    """Test edge cases and combined patterns."""

    def test_mixed_severity_takes_highest(self):
        """When multiple severity levels match, highest should be returned."""
        result = detect_harassment("バカ！殺すぞ！困る！")
        assert result.severity == Severity.CRITICAL  # "殺す" is critical

    def test_katakana_detection(self):
        result = detect_harassment("コロス")
        assert result.severity == Severity.CRITICAL

    def test_hiragana_detection(self):
        result = detect_harassment("ばか")
        assert result.severity == Severity.HIGH

    def test_recommendation_for_critical(self):
        result = detect_harassment("殺す")
        assert "エスカレーション" in result.recommendation

    def test_recommendation_for_high(self):
        result = detect_harassment("バカ")
        assert "引き継ぎ" in result.recommendation or "上席" in result.recommendation
