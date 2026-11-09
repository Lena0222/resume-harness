from __future__ import annotations

import logging
from pathlib import Path

from core.types import (
    JobPosting,
    GeneratedResume,
    PipelineResult,
    ReviewResult,
    FigmaExportResult,
)
from agents.input_parser import InputParserAgent
from agents.matching import MatchingAgent
from agents.writing import WritingAgent
from agents.review import ReviewAgent
from agents.figma import FigmaAgent

logger = logging.getLogger(__name__)


class ResumePipeline:
    def __init__(self, master_resume_path: Path, figma_template_id: str = ""):
        self.master_resume_path = master_resume_path
        self.figma_template_id = figma_template_id

        self.input_parser = InputParserAgent()
        self.matching = MatchingAgent(master_resume_path)
        self.writing = WritingAgent()
        self.review = ReviewAgent()
        self.figma = FigmaAgent(figma_template_id)

    async def run(self, job_posting_text: str, skip_figma: bool = False) -> PipelineResult:
        logger.info("파이프라인 시작")

        # 1. 공고 파싱
        logger.info("[1/5] 공고 파싱")
        job_posting: JobPosting = await self.input_parser.parse(job_posting_text)

        # 2. 마스터 이력서 매칭
        logger.info("[2/5] 항목 매칭")
        matched_items = await self.matching.match(job_posting)

        # 3. 이력서 작성
        logger.info("[3/5] 이력서 작성")
        generated_resume: GeneratedResume = await self.writing.write(job_posting, matched_items)

        # 4. 검토
        logger.info("[4/5] 이력서 검토")
        review: ReviewResult = await self.review.review(generated_resume)

        # 5. Figma 삽입 및 PDF 내보내기
        figma_result = FigmaExportResult(success=False)
        if not skip_figma:
            logger.info("[5/5] Figma 내보내기")
            figma_result = await self.figma.export(generated_resume)

        logger.info("파이프라인 완료")
        return PipelineResult(
            job_posting=job_posting,
            generated_resume=generated_resume,
            review=review,
            figma_export=figma_result,
        )
