from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic
import yaml

from core.types import JobPosting, MasterResumeItem, MatchedItem

SYSTEM_PROMPT = """\
당신은 이력서 매칭 전문가입니다.
마스터 이력서의 항목들과 채용 공고의 요건을 비교하여 각 항목의 관련성 점수(0.0~1.0)와 이유를 평가하세요.

반환 형식 (JSON 배열):
[
  {
    "id": "항목 id",
    "score": 0.95,
    "reasons": ["관련성 이유1", "이유2"]
  },
  ...
]

점수 기준:
- 0.8~1.0: 직접적으로 요구되는 기술/경험
- 0.5~0.8: 관련성 있는 경험
- 0.2~0.5: 간접적으로 도움이 되는 경험
- 0.0~0.2: 관련성 낮음

JSON만 반환하고 다른 텍스트는 포함하지 마세요.
"""


class MatchingAgent:
    def __init__(self, master_resume_path: Path):
        self.master_resume_path = master_resume_path
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._items: list[MasterResumeItem] | None = None

    def _load_master(self) -> list[MasterResumeItem]:
        if self._items is not None:
            return self._items

        raw = yaml.safe_load(self.master_resume_path.read_text(encoding="utf-8"))
        items = []
        sections = raw.get("sections", {})

        for section_name, entries in sections.items():
            for entry in entries:
                # experience 섹션은 achievements를 개별 항목으로 풀어서 인덱싱
                if section_name == "experience" and "achievements" in entry:
                    company = entry.get("company", "")
                    for ach in entry["achievements"]:
                        items.append(
                            MasterResumeItem(
                                id=ach["id"],
                                section="experience",
                                title=f"{company} — {ach['title']}",
                                description=ach.get("description", ""),
                                tags=ach.get("tags", []),
                                raw={**ach, "_company": company, "_exp_id": entry["id"]},
                            )
                        )
                    # 회사 단위 요약도 항목으로 추가
                    items.append(
                        MasterResumeItem(
                            id=entry["id"],
                            section="experience_summary",
                            title=f"{company} {entry.get('title', '')}",
                            description=entry.get("summary", ""),
                            tags=[entry.get("role", "")],
                            raw=entry,
                        )
                    )
                else:
                    items.append(
                        MasterResumeItem(
                            id=entry["id"],
                            section=section_name,
                            title=entry["title"],
                            description=entry.get("description", ""),
                            tags=entry.get("tags", []),
                            raw=entry,
                        )
                    )

        self._items = items
        return items

    async def match(self, job_posting: JobPosting) -> list[MatchedItem]:
        items = self._load_master()

        items_text = json.dumps(
            [{"id": i.id, "title": i.title, "description": i.description, "tags": i.tags} for i in items],
            ensure_ascii=False,
        )
        posting_text = json.dumps(
            {
                "role": job_posting.role,
                "required_skills": job_posting.required_skills,
                "preferred_skills": job_posting.preferred_skills,
                "keywords": job_posting.keywords,
            },
            ensure_ascii=False,
        )

        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"마스터 이력서 항목:\n{items_text}\n\n채용 공고:\n{posting_text}",
                }
            ],
        )

        scores: list[dict] = json.loads(message.content[0].text)
        score_map = {s["id"]: s for s in scores}

        matched = []
        for item in items:
            score_data = score_map.get(item.id, {"score": 0.0, "reasons": []})
            if score_data["score"] >= 0.2:
                matched.append(
                    MatchedItem(
                        item=item,
                        score=score_data["score"],
                        reasons=score_data.get("reasons", []),
                    )
                )

        return sorted(matched, key=lambda x: x.score, reverse=True)
