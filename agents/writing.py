from __future__ import annotations

import json
import os

import anthropic

from core.types import GeneratedResume, JobPosting, MatchedItem, ResumeSection

SYSTEM_PROMPT = """\
당신은 전문 이력서 작성자입니다.
채용 공고와 매칭된 경험 항목들을 바탕으로 지원자의 이력서 각 섹션을 작성하세요.

작성 원칙:
- 공고의 키워드와 요구사항을 자연스럽게 반영
- 수치와 성과를 구체적으로 기술
- 간결하고 임팩트 있는 문장 사용
- 한국어로 작성 (회사/기술명 등 고유명사는 원어 유지)

반환 형식 (JSON):
{
  "sections": [
    {"section": "summary", "content": "직무 요약 2~3문장"},
    {"section": "experience", "content": "경력 기술 (마크다운 불릿 형식)"},
    {"section": "projects", "content": "프로젝트 기술"},
    {"section": "skills", "content": "기술 스택 목록"}
  ]
}

JSON만 반환하고 다른 텍스트는 포함하지 마세요.
"""


class WritingAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    async def write(self, job_posting: JobPosting, matched_items: list[MatchedItem]) -> GeneratedResume:
        top_items = matched_items[:10]

        context = {
            "job": {
                "company": job_posting.company,
                "role": job_posting.role,
                "required_skills": job_posting.required_skills,
                "keywords": job_posting.keywords,
            },
            "matched_items": [
                {
                    "section": m.item.section,
                    "title": m.item.title,
                    "description": m.item.description,
                    "score": m.score,
                    "reasons": m.reasons,
                }
                for m in top_items
            ],
        }

        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False),
                }
            ],
        )

        data = json.loads(message.content[0].text)
        sections = [ResumeSection(**s) for s in data["sections"]]

        return GeneratedResume(
            job_posting=job_posting,
            sections=sections,
            matched_items=matched_items,
        )
