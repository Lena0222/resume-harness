# 이력서 제작 하네스

## 가장 중요한 규칙

**PRD.md에 없는 내용은 구현 전 사용자에게 먼저 확인한다. 그럴듯하게 채우거나 추측하지 않는다.**

게이트 전체 목록 → `PRD.md` 섹션 5 참고

---

## 프로젝트 개요

마스터 이력서를 읽어서 채용 공고에 맞게 자동으로 이력서를 생성하고, Figma 템플릿에 삽입한 후 PDF로 내보내는 멀티에이전트 시스템.

서비스 정의·사용자 시나리오·플로우 전체 → `PRD.md` 참고

---

## 에이전트 파이프라인

```
InputParserAgent → MatchingAgent → (NotionAgent) → WritingAgent → ReviewAgent → FigmaAgent
```

각 에이전트 역할 → `PRD.md` 섹션 4 참고

---

## 디렉토리 구조

```
.
├── agents/          # 각 에이전트 모듈
├── core/            # 파이프라인 오케스트레이터, 공통 타입
├── data/
│   ├── master/      # 마스터 이력서 파일
│   │   ├── 이력서_master.md      # 원본 (수동 관리)
│   │   ├── resume.yaml    # 파이프라인 소스 (md 기반 구조화)
│   │   └── resume.yaml           # 폼 템플릿 (참고용)
│   ├── outputs/     # 생성된 이력서 결과물
│   └── templates/   # Figma 템플릿 메타데이터
├── config/          # API 키, Figma 설정
├── PRD.md           # 서비스 정의·게이트·미확정 항목
├── design.md        # 디자인 규칙 (추후 작성)
└── tests/
```

---

## 개발 규칙

- Python 3.11+, `anthropic` SDK 사용
- 에이전트 간 통신: `core/types.py`의 Pydantic 모델 사용
- 비동기(`asyncio`) 기반
- API 키는 `.env`에서 로드 (하드코딩 금지)
- Figma 연동: figma-desktop MCP (`use_figma`, `get_metadata`, `get_screenshot`)
- 노션 연동: Notion MCP
