from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    raw_text: str
    company: str = ""
    role: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class MasterResumeItem(BaseModel):
    """마스터 이력서의 단일 경험/프로젝트/기술 항목"""
    id: str
    section: str  # "experience" | "project" | "skill" | "education"
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class MatchedItem(BaseModel):
    item: MasterResumeItem
    score: float  # 0.0 ~ 1.0
    reasons: list[str] = Field(default_factory=list)


class ResumeSection(BaseModel):
    section: str
    content: str


class GeneratedResume(BaseModel):
    job_posting: JobPosting
    sections: list[ResumeSection]
    matched_items: list[MatchedItem]


class ReviewResult(BaseModel):
    score: int  # 0 ~ 100
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    approved: bool


class FigmaExportResult(BaseModel):
    figma_file_url: str = ""
    pdf_path: str = ""
    success: bool
    error: str = ""


class PipelineResult(BaseModel):
    job_posting: JobPosting
    generated_resume: GeneratedResume
    review: ReviewResult
    figma_export: FigmaExportResult
