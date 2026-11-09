from __future__ import annotations

import json
import os

import anthropic

from core.types import JobPosting

SYSTEM_PROMPT = """\
당신은 채용 공고를 분석하는 전문가입니다.
주어진 채용 공고 텍스트를 파싱하여 다음 항목을 JSON으로 반환하세요.

반환 형식:
{
  "company": "회사명",
  "role": "직무명",
  "required_skills": ["필수 기술/자격 목록"],
  "preferred_skills": ["우대 기술/자격 목록"],
  "responsibilities": ["주요 업무 목록"],
  "keywords": ["핵심 키워드 목록 (최대 15개)"]
}

JSON만 반환하고 다른 텍스트는 포함하지 마세요.
"""


class InputParserAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    async def parse(self, raw_text: str) -> JobPosting:
        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": raw_text}],
        )
        data = json.loads(message.content[0].text)
        return JobPosting(raw_text=raw_text, **data)
