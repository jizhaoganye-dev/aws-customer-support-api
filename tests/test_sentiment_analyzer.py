"""
Unit tests for sentiment_analyzer module.
Tests sentiment classification, anger detection, and alert triggering.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'layers', 'common', 'python'))

from sentiment_analyzer import analyze_sentiment, Sentiment


class TestSentimentAnalyzer:
    """Test sentiment analysis and anger detection."""

    # ── Positive sentiment tests ──────────────────────────────────────────

    def test_positive_thanks(self):
        result = analyze_sentiment("ありがとうございます！助かりました！")
        assert result.sentiment == Sentiment.POSITIVE
        assert result.trigger_alert is False

    def test_positive_satisfaction(self):
        result = analyze_sentiment("素晴らしいサービスですね。完璧です。")
        assert result.sentiment == Sentiment.POSITIVE

    # ── Negative sentiment tests ──────────────────────────────────────────

    def test_negative_complaint(self):
        result = analyze_sentiment("不満です。残念な対応でした。がっかりです。")
        assert result.sentiment == Sentiment.NEGATIVE

    def test_negative_problem(self):
        result = analyze_sentiment("エラーが出て使えません。バグだと思います。")
        assert result.sentiment == Sentiment.NEGATIVE

    # ── Anger sentiment tests (with alert) ────────────────────────────────

    def test_anger_explicit(self):
        result = analyze_sentiment("ふざけるな！許せない！最悪だ！")
        assert result.sentiment == Sentiment.ANGER
        assert result.trigger_alert is True

    def test_anger_frustration(self):
        result = analyze_sentiment("いい加減にしろ！腹が立つ！")
        assert result.sentiment == Sentiment.ANGER
        assert result.trigger_alert is True

    def test_anger_insult(self):
        result = analyze_sentiment("バカ！クソ対応！ムカつく！")
        assert result.sentiment == Sentiment.ANGER
        assert result.trigger_alert is True

    def test_anger_single_keyword(self):
        result = analyze_sentiment("ひどい対応ですね")
        assert result.sentiment == Sentiment.ANGER
        assert result.trigger_alert is True

    # ── Neutral sentiment tests ───────────────────────────────────────────

    def test_neutral_question(self):
        result = analyze_sentiment("注文状況を確認したいです")
        assert result.sentiment == Sentiment.NEUTRAL

    def test_neutral_empty(self):
        result = analyze_sentiment("")
        assert result.sentiment == Sentiment.NEUTRAL
        assert result.trigger_alert is False

    # ── Confidence tests ──────────────────────────────────────────────────

    def test_strong_anger_high_confidence(self):
        result = analyze_sentiment("ふざけるな！最悪！許せない！ムカつく！")
        assert result.confidence >= 0.8

    def test_mild_sentiment_lower_confidence(self):
        result = analyze_sentiment("ちょっと困っています")
        assert result.confidence <= 0.8

    # ── Score structure tests ─────────────────────────────────────────────

    def test_scores_sum_to_one(self):
        result = analyze_sentiment("ありがとう、でも少し不満もあります")
        total = sum(result.scores.values())
        assert abs(total - 1.0) < 0.01  # Allow small floating point error

    def test_scores_keys(self):
        result = analyze_sentiment("テスト")
        assert set(result.scores.keys()) == {"positive", "neutral", "negative", "anger"}

    # ── Serialization tests ───────────────────────────────────────────────

    def test_to_dict(self):
        result = analyze_sentiment("テスト")
        d = result.to_dict()
        assert "sentiment" in d
        assert "confidence" in d
        assert "scores" in d
        assert "trigger_alert" in d
        assert "keywords_found" in d
        assert isinstance(d["sentiment"], str)

    # ── Exclamation boost test ────────────────────────────────────────────

    def test_exclamation_boosts_anger(self):
        result_calm = analyze_sentiment("最悪")
        result_excited = analyze_sentiment("最悪！！！！！")
        assert result_excited.confidence >= result_calm.confidence
