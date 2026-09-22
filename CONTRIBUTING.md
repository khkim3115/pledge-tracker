# 기여 가이드

## 운영 원칙

- **정치적 중립**: 커밋 메시지·이슈·PR·코드 주석에 개인의 정치적 의견이나 특정 인물·정당에 대한 평가를 쓰지 않습니다. 사실과 출처만 기록합니다.
- **표현**: 지자체 자가보고와 근거의 차이는 "공개 자료와의 차이"처럼 사실로만 기술합니다. "허위", "거짓" 같은 평가어는 쓰지 않습니다.
- **시크릿**: 인증키·토큰은 절대 커밋하지 않습니다. `pre-commit install`로 gitleaks 훅을 켜 두세요. 공공데이터포털 인증키는 약관상 제3자 공유 금지입니다.
- **정정 요청**: 판정 오류·데이터 오류 제보는 이슈로 받습니다. 근거 재검토 후 판정이 바뀌면 이전 판정과 변경 이력을 함께 공개합니다.

## 새 지역(어댑터) 추가하기

이행 현황이 지원되지 않는 지역은 어댑터 하나로 추가할 수 있습니다.
공통 인터페이스는 [`pipeline/src/pledge_pipeline/adapters/base.py`](pipeline/src/pledge_pipeline/adapters/base.py)의 `Adapter`입니다.

1. **사전 조사** — 해당 지자체의 공약 추진현황 페이지를 확인하고 PR 본문에 적어 주세요.
   - 입구 URL, 형식(HTML 표 / 게시판 첨부 PDF·HWP·XLSX), 갱신 주기와 최신 기준 시점
   - 과제별 필드(과제명, 부서, 예산, 추진상태, 진척률, 실적)와 **추진상태 원문 값 목록**
   - `robots.txt`, 공공누리 유형, 해외 IP 접근 가능 여부(`python scripts/probe_access.py`에 대상 추가 후 실행)
2. **설정** — `adapter_id`, `region`, `term`, `base_url`, `parser_type`, `status_mapping`(원문 상태값 → 표준 5분류: `completed` 완료 / `continuing` 이행후계속추진 / `on_track` 정상추진 / `partial` 일부추진 / `stalled` 보류·폐기).
   애매한 상태값은 추측해서 매핑하지 말고 PR에서 논의합니다.
3. **파서** — `fetch()`로 원천 문서를 가져오고 `parse()`에서 `ParsedTask`를 만듭니다. 값은 원문 그대로 두고, 정규화는 `normalize()`에 맡깁니다.
4. **테스트 픽스처** — 실제 페이지/문서 1~2개를 `pipeline/tests/fixtures/<adapter_id>/`에 저장하고(공공누리 유형이 재배포를 허용하는 경우), 파서 결과를 검증하는 테스트를 추가합니다. 네트워크 없이 통과해야 합니다.

## 개발

```bash
pip install -e "pipeline[dev]"
pre-commit install
ruff check . && ruff format --check .
pytest pipeline
```
