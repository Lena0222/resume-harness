#!/usr/bin/env python3
"""이력서 제작 하네스 CLI"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

MASTER_RESUME = Path(__file__).parent / "data" / "master" / "resume.yaml"
OUTPUTS_DIR = Path(__file__).parent / "data" / "outputs"


async def run(job_posting_text: str, figma_template_id: str, skip_figma: bool) -> None:
    from core.pipeline import ResumePipeline

    pipeline = ResumePipeline(
        master_resume_path=MASTER_RESUME,
        figma_template_id=figma_template_id,
    )

    result = await pipeline.run(job_posting_text, skip_figma=skip_figma)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    company = result.job_posting.company or "unknown"
    role = result.job_posting.role or "role"
    output_path = OUTPUTS_DIR / f"{company}_{role}_resume.json"
    output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"회사: {result.job_posting.company}")
    print(f"직무: {result.job_posting.role}")
    print(f"검토 점수: {result.review.score}/100 ({'승인' if result.review.approved else '재검토 필요'})")
    if result.review.issues:
        print(f"이슈: {', '.join(result.review.issues)}")
    print(f"결과 저장: {output_path}")
    if result.figma_export.success:
        print(f"Figma: {result.figma_export.figma_file_url}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="이력서 제작 하네스")
    parser.add_argument("posting", nargs="?", help="채용 공고 텍스트 또는 파일 경로")
    parser.add_argument("--figma-template", default="", help="Figma 템플릿 파일 ID")
    parser.add_argument("--skip-figma", action="store_true", help="Figma 단계 건너뜀")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("오류: ANTHROPIC_API_KEY 환경변수를 설정하세요.")

    if args.posting:
        p = Path(args.posting)
        job_text = p.read_text(encoding="utf-8") if p.exists() else args.posting
    else:
        print("채용 공고를 붙여넣고 빈 줄 두 개로 종료하세요:")
        lines = []
        blank_count = 0
        for line in sys.stdin:
            if line.strip() == "":
                blank_count += 1
                if blank_count >= 2:
                    break
            else:
                blank_count = 0
            lines.append(line)
        job_text = "".join(lines)

    asyncio.run(run(job_text, args.figma_template, args.skip_figma))


if __name__ == "__main__":
    main()
