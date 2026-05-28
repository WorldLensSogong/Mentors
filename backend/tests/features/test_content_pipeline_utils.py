"""콘텐츠 동 순수함수 테스트. 외부 의존 없음 — fast."""

from datetime import datetime, timedelta, timezone

import pytest

from core.contracts import MentorStrategy
from features.content import pipeline_utils as pu


class TestCanonicalizeURL:
    def test_strips_utm_params(self) -> None:
        url = "https://example.com/news?utm_source=twitter&utm_campaign=x&id=42"
        out = pu.canonicalize_url(url)
        assert "utm_source" not in out
        assert "utm_campaign" not in out
        assert "id=42" in out

    def test_strips_fragment(self) -> None:
        assert pu.canonicalize_url("https://a.com/x#y") == "https://a.com/x"

    def test_lowercases_host(self) -> None:
        assert pu.canonicalize_url("https://EXAMPLE.COM/X").startswith("https://example.com/")

    def test_idempotent(self) -> None:
        url = "https://example.com/news?id=42"
        assert pu.canonicalize_url(pu.canonicalize_url(url)) == pu.canonicalize_url(url)


class TestStripHTML:
    def test_removes_tags(self) -> None:
        assert pu.strip_html("<p>hello <b>world</b></p>") == "hello world"

    def test_collapses_whitespace(self) -> None:
        assert pu.strip_html("a   b\n\nc") == "a b c"

    def test_empty_input(self) -> None:
        assert pu.strip_html(None) == ""
        assert pu.strip_html("") == ""


class TestRSSMetadataDetection:
    def test_short_content_treated_as_metadata(self) -> None:
        assert pu.looks_like_rss_metadata("<p>too short</p>") is True

    def test_none_treated_as_metadata(self) -> None:
        assert pu.looks_like_rss_metadata(None) is True

    def test_proper_article_not_metadata(self) -> None:
        body = "This is a properly long article body. " * 30
        assert pu.looks_like_rss_metadata(body) is False


class TestReliabilityScore:
    def test_high_score_for_reuters_recent_long_content(self) -> None:
        score, level, _ = pu.reliability_score(
            source_name="Reuters",
            content="Long article. " * 50 + "Numbers: 12%, 45%, 78%, GDP 3.2%, " * 5,
            published_at=datetime.now(timezone.utc) - timedelta(hours=2),
            title="Important economic news",
        )
        assert score >= 70
        assert level in ("high", "very_high")

    def test_clickbait_penalty(self) -> None:
        score_no_cb, _, _ = pu.reliability_score(
            source_name="Reuters",
            content="content " * 100,
            published_at=datetime.now(timezone.utc),
            title="Earnings beat expectations",
        )
        score_cb, _, _ = pu.reliability_score(
            source_name="Reuters",
            content="content " * 100,
            published_at=datetime.now(timezone.utc),
            title="충격! 당신은 절대 안 믿을 것이다",
        )
        assert score_cb < score_no_cb

    def test_low_score_for_unknown_source(self) -> None:
        score, level, _ = pu.reliability_score(
            source_name="random-blog",
            content=None,
            published_at=None,
            title="something",
        )
        assert score <= 40
        assert level == "low"


class TestEconomyClassification:
    def test_korean_economy_terms_detected(self) -> None:
        assert pu.is_economy("코스피 3% 상승", "외국인 매수세 유입", language="ko") is True

    def test_english_economy_terms_detected(self) -> None:
        assert pu.is_economy("Stock surges on earnings beat", None, language="en") is True

    def test_non_economy_returns_false(self) -> None:
        assert pu.is_economy("오늘 날씨 맑음", "기온 22도", language="ko") is False


class TestStrategyClassification:
    @pytest.mark.parametrize(
        "title,expected",
        [
            ("배당수익률 5% 종목 추천", MentorStrategy.DIVIDEND),
            ("매출 성장 30% 가이던스 상향", MentorStrategy.GROWTH),
            ("저PER 가치주 발굴", MentorStrategy.VALUE),
            ("주가 급등 거래량 증가", MentorStrategy.MOMENTUM),
        ],
    )
    def test_detects_strategy(self, title: str, expected: MentorStrategy) -> None:
        result = pu.classify_strategies(title, None)
        assert expected in result

    def test_empty_when_no_hints(self) -> None:
        assert pu.classify_strategies("일반 기사 제목입니다", None) == []
