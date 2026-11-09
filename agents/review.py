from __future__ import annotations

import json
import os

import anthropic

from core.types import GeneratedResume, ReviewResult

SYSTEM_PROMPT = """\
당신은 채용 전문가로서 이력서를 검토합니다.
생성된 이력서 내용을 평가하고 개선 사항을 제안하세요.

평가 기준:
- 공고 요건과의 일치도 (40점)
- 내용의 구체성과 수치화 (20점)
- 가독성과 구성 (20점)
- 키워드 최적화 (20점)

반환 형식 (JSON):
{
  "score": 85,
  "approved": true,
  "issues": ["발견된 문제점 목록"],
  "suggestions": ["개선 제안 목록"]
}

승인 기준: score >= 70
JSON만 반환하고 다른 텍스트는 포함하지 마세요.
"""


class ReviewAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    async def review(self, resume: GeneratedResume) -> ReviewResult:
        content = {
            "job_posting": {
                "role": resume.job_posting.role,
                "required_skills": resume.job_posting.required_skills,
                "keywords": resume.job_posting.keywords,
            },
            "resume_sections": [
                {"section": s.section, "content": s.content} for s in resume.sections
            ],
        }

        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(content, ensure_ascii=False),
                }
            ],
        )

        data = json.loads(message.content[0].text)
        return ReviewResult(**data)
