from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.mentor_repository import get_mentor_model
from app.repositories.news_repository import list_recent_article_models
from app.repositories.user_repository import get_user_or_404
from app.schemas.report import ReportPreviewRequest, ReportPreviewResult


def build_report_preview(db: Session, payload: ReportPreviewRequest) -> ReportPreviewResult:
    user = get_user_or_404(db, payload.user_id)
    mentor = get_mentor_model(db, payload.mentor_id)
    recent_articles = list_recent_article_models(db, limit=3)

    article_titles = [article.title for article in recent_articles]
    headline_summary = ", ".join(article_titles) if article_titles else "아직 연결된 뉴스 데이터가 없습니다"

    summary_text = (
        f"{user.nickname}님의 현재 학습 멘토는 {mentor.name}이며, "
        f"최근 주요 이슈는 {headline_summary} 입니다."
    )
    outlook_text = (
        f"{mentor.strategy.name} 관점에서는 단기 변동성보다 "
        f"정보를 구조화해서 해석하는 연습이 우선입니다."
    )
    learning_question_text = (
        "오늘 확인한 뉴스 중 하나를 골라, 왜 중요한지 자신의 말로 설명해볼 수 있나요?"
    )

    return ReportPreviewResult(
        title=f"{mentor.name}의 오늘의 시장 브리핑",
        summary_text=summary_text,
        outlook_text=outlook_text,
        learning_question_text=learning_question_text,
    )

