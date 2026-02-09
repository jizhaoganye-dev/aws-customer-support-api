"""
Harassment detection engine for customer support messages.
Rule-based + AI-enhanced (Claude Opus 4.6 / Gemini 3) analysis.
"""
import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class HarassmentResult:
    is_harassment: bool
    severity: Severity
    confidence: float
    matched_patterns: list[str]
    categories: list[str]
    recommendation: str

    def to_dict(self) -> dict:
        return {
            "is_harassment": self.is_harassment,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "matched_patterns": self.matched_patterns,
            "categories": self.categories,
            "recommendation": self.recommendation,
        }


# ── Pattern Definitions ──────────────────────────────────────────────────────

CRITICAL_PATTERNS = [
    # Direct threats
    (r"殺す|ころす|コロス", "death_threat"),
    (r"死ね|しね|シネ", "death_wish"),
    (r"爆破|放火|刺す", "violence_threat"),
    (r"訴え(る|てやる)|裁判|弁護士呼ぶ", "legal_threat"),
    (r"(上|部)長.*出せ.*殺|殺.*上.*出せ", "escalation_threat"),
]

HIGH_PATTERNS = [
    # Severe insults
    (r"バカ|ばか|馬鹿", "insult_baka"),
    (r"アホ|あほ|阿呆", "insult_aho"),
    (r"カス|かす|クズ|くず|屑", "insult_kasu"),
    (r"ゴミ|ごみ|ゴミクズ", "insult_gomi"),
    (r"キチガイ|きちがい|基地外", "insult_kichigai"),
    (r"ふざけるな|ふざけんな|ナメてる|舐めてる", "contempt"),
    (r"能無し|無能|役立たず|使えない", "incompetence_insult"),
    (r"ボケ|ぼけ|ドアホ", "insult_boke"),
    (r"クソ|くそ|糞", "insult_kuso"),
    (r"ブス|デブ|ハゲ|キモい|きもい", "appearance_insult"),
]

MEDIUM_PATTERNS = [
    # Aggressive demands / intimidation
    (r"今すぐ|すぐに|直ちに|至急", "urgency_pressure"),
    (r"責任.*取れ|責任者.*出せ|上の者", "escalation_demand"),
    (r"金.*返せ|弁償しろ|賠償", "compensation_demand"),
    (r"(SNS|ネット|Twitter|X).*晒す|拡散", "social_media_threat"),
    (r"二度と.*使わない|解約.*してやる", "service_threat"),
    (r"いい加減に|何回.*言え|何度も", "frustration_repeat"),
]

LOW_PATTERNS = [
    # Mild frustration
    (r"困る|困って|不便", "frustration"),
    (r"遅い|遅すぎ|待たされ", "complaint_slow"),
    (r"分かりにくい|説明.*ない|不親切", "complaint_unclear"),
]


def detect_harassment(text: str) -> HarassmentResult:
    """
    Detect harassment in the given text using pattern matching.

    Args:
        text: The user message to analyze.

    Returns:
        HarassmentResult with severity, confidence, and matched patterns.
    """
    if not text or not text.strip():
        return HarassmentResult(
            is_harassment=False,
            severity=Severity.NONE,
            confidence=1.0,
            matched_patterns=[],
            categories=[],
            recommendation="入力なし",
        )

    matched_patterns = []
    categories = set()
    max_severity = Severity.NONE
    severity_scores = {Severity.CRITICAL: 4, Severity.HIGH: 3, Severity.MEDIUM: 2, Severity.LOW: 1, Severity.NONE: 0}

    # Check all pattern groups
    for patterns, severity in [
        (CRITICAL_PATTERNS, Severity.CRITICAL),
        (HIGH_PATTERNS, Severity.HIGH),
        (MEDIUM_PATTERNS, Severity.MEDIUM),
        (LOW_PATTERNS, Severity.LOW),
    ]:
        for pattern, category in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matched_patterns.append(pattern)
                categories.add(category)
                if severity_scores[severity] > severity_scores[max_severity]:
                    max_severity = severity

    is_harassment = max_severity in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM)

    # Calculate confidence based on number of matches
    match_count = len(matched_patterns)
    if match_count == 0:
        confidence = 0.9  # High confidence it's NOT harassment
    elif match_count == 1:
        confidence = 0.7
    elif match_count <= 3:
        confidence = 0.85
    else:
        confidence = 0.95

    # Generate recommendation
    recommendations = {
        Severity.CRITICAL: "即座に上席者へエスカレーション。通話録音を保存し、法務部門に報告してください。",
        Severity.HIGH: "冷静に対応し、上席者への引き継ぎを準備してください。対応履歴を詳細に記録してください。",
        Severity.MEDIUM: "落ち着いたトーンで対応を継続。感情的にならず、事実ベースで回答してください。",
        Severity.LOW: "通常対応を継続。お客様の不満に寄り添いながら解決策を提示してください。",
        Severity.NONE: "通常対応を継続してください。",
    }

    return HarassmentResult(
        is_harassment=is_harassment,
        severity=max_severity,
        confidence=confidence,
        matched_patterns=matched_patterns,
        categories=sorted(categories),
        recommendation=recommendations[max_severity],
    )
