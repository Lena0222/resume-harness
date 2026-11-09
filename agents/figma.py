from __future__ import annotations

"""
Figma 에이전트 — figma-desktop MCP 사용
흐름:
  1. get_metadata     → 템플릿 파일의 텍스트 노드 목록 확인
  2. use_figma (JS)   → 각 텍스트 노드에 이력서 내용 삽입
  3. get_screenshot   → 결과 확인
  4. use_figma (JS)   → PDF 내보내기 (Figma REST API 활용)

이 모듈은 파이프라인에서 호출되는 순수 데이터 준비 레이어.
실제 MCP 도구 호출은 Claude가 tool_use로 직접 수행.
"""

from core.types import FigmaExportResult, GeneratedResume

# Figma 텍스트 노드 이름 → 이력서 섹션 매핑
# 실제 Figma 템플릿의 노드 이름에 맞게 수정 필요
SECTION_TO_NODE: dict[str, str] = {
    "summary": "text/summary",
    "experience": "text/experience",
    "projects": "text/projects",
    "skills": "text/skills",
    "cover_letter": "text/cover_letter",
}


class FigmaAgent:
    def __init__(self, template_file_id: str):
        self.template_file_id = template_file_id

    def build_node_updates(self, resume: GeneratedResume) -> list[dict]:
        """섹션 텍스트를 Figma 노드 업데이트 명령 목록으로 변환"""
        updates = []
        for section in resume.sections:
            node_name = SECTION_TO_NODE.get(section.section, f"text/{section.section}")
            updates.append({"node_name": node_name, "text": section.content})
        return updates

    def build_figma_script(self, node_updates: list[dict]) -> str:
        """use_figma에 전달할 JS 코드 생성 — 노드 이름으로 텍스트 노드를 찾아 내용 교체"""
        lines = ["const page = figma.currentPage;"]
        for update in node_updates:
            escaped = update["text"].replace("`", "\\`").replace("\\", "\\\\")
            lines.append(
                f'const node_{update["node_name"].replace("/", "_")} = '
                f'page.findOne(n => n.name === "{update["node_name"]}" && n.type === "TEXT");'
            )
            lines.append(
                f'if (node_{update["node_name"].replace("/", "_")}) {{'
                f'  await figma.loadFontAsync(node_{update["node_name"].replace("/", "_")}.fontName);'
                f'  node_{update["node_name"].replace("/", "_")}.characters = `{escaped}`;'
                f"}}"
            )
        return "\n".join(lines)

    async def export(self, resume: GeneratedResume) -> FigmaExportResult:
        if not self.template_file_id:
            return FigmaExportResult(
                success=False,
                error="FIGMA_TEMPLATE_FILE_ID가 설정되지 않았습니다. --figma-template 플래그로 전달하세요.",
            )

        node_updates = self.build_node_updates(resume)
        script = self.build_figma_script(node_updates)

        # 실제 MCP 호출은 main.py의 interactive Figma 모드 또는
        # Claude가 tool_use로 직접 수행 (get_metadata → use_figma → get_screenshot)
        return FigmaExportResult(
            success=False,
            error=(
                f"Figma 삽입 준비 완료. "
                f"파일 ID: {self.template_file_id}, "
                f"업데이트 노드: {len(node_updates)}개. "
                f"Figma 데스크탑에서 파일을 열고 `python main.py --figma` 로 실행하세요."
            ),
        )
