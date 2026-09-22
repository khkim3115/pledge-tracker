# pledge-tracker (가칭)

지방자치단체장·교육감 공약의 **이행 현황을 자동 수집·판정·통합 조회**하는 오픈소스 서비스.

- **통합 조회** — 선관위 공약 데이터(전국) + 지자체별 이행 추적을 한 곳에서
- **검증 가능한 AI 판정** — 모든 판정에 근거 문단·원문 링크·수집 시점을 연결
- **불일치 탐지** — 지자체 자가보고와 실제 근거 사이의 차이를 사실 그대로 표시

전체 기획·범위·중립성 정책은 [docs/PROJECT.md](docs/PROJECT.md)를 참고하세요.

> 상태: 1주차 — 레포 초기화, 스키마 초안, 선관위 API 수집기, 경기·서울 페이지 구조 조사.

## 레포 구조

```text
pipeline/               Python 수집·처리 파이프라인 (선관위 API 수집기, 지자체 어댑터)
supabase/migrations/    PostgreSQL + pgvector 스키마 (Supabase)
scripts/                운영 스크립트 (접근성 프로브 등)
.github/workflows/      배치·유휴 방지 핑·접근성 프로브·시크릿 스캔
docs/                   기획 문서, 조사 기록
```

웹(Nuxt 3)은 5–6주차에 `web/`으로 추가 예정입니다.

## 개발 환경

```bash
# 1) 시크릿: .env.example을 복사해 값 채우기 (.env는 커밋되지 않음)
cp .env.example .env

# 2) 파이프라인 (Python 3.12 권장, 3.11 이상)
python -m venv .venv
.venv/Scripts/activate        # macOS/Linux: source .venv/bin/activate
pip install -e "pipeline[dev]"

# 3) 시크릿 유출 방지 훅 (gitleaks)
pip install pre-commit
pre-commit install
```

선관위 API 수집 예시:

```bash
python -m pledge_pipeline.nec.collect --sg-id 20220601
```

## 시크릿 위생

- 키는 로컬 `.env` 또는 **GitHub Secrets**로만 주입합니다. `.env`는 gitignore, `.env.example`만 커밋합니다.
- 커밋 시 gitleaks pre-commit 훅이, push/PR 시 `secret-scan` 워크플로가 검사합니다.
- 공공데이터포털 인증키는 이용약관상 제3자 공유가 금지되어 있습니다. 이슈·PR·로그에 붙여넣지 마세요.

## 기여

어댑터(지자체) 추가 방법과 레포 운영 원칙은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.
이 레포(커밋 메시지·이슈·PR 포함)에서는 개인의 정치적 의견 표명을 하지 않습니다.

## 라이선스

- **코드**: [Apache License 2.0](LICENSE)
- **데이터**(판정 결과·이행률 등 이 프로젝트가 생산한 데이터셋): [CC BY 4.0](DATA_LICENSE.md)
- **상표 제외**: 서비스명·로고는 위 라이선스의 허여 범위에 포함되지 않습니다(Apache-2.0 제6조). 포크·파생 서비스는 다른 이름과 로고를 사용해야 합니다. 자세한 내용은 [NOTICE](NOTICE) 참고.
- 원천 자료(선관위·지자체 공개 자료)의 권리는 각 출처에 있으며, 출처별 공공누리 유형을 따릅니다.
