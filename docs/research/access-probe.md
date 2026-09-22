# 접근성 프로브 결과: 국내 PC vs GitHub Actions(해외)

- 측정일: 2026-09-22
- 도구: [`scripts/probe_access.py`](../../scripts/probe_access.py) (대상: [`scripts/probe_targets.json`](../../scripts/probe_targets.json)), 워크플로 [`probe-kr-access.yml`](../../.github/workflows/probe-kr-access.yml)
- Actions 러너 위치: `US Iowa, AS8075 Microsoft Corporation` (ipinfo.io 기준)
- 판정 기준: 20초 안에 응답이 없으면 `timeout`. 키 없이 호출한 API의 401은 "서버 도달"로 보고 `ok`로 처리

## 결과

| 대상 | 국내 PC | GitHub Actions (3회) |
| :- | :- | :- |
| data.go.kr 당선인정보 API | ok (401, 키 없음) | **timeout** ×3 |
| data.go.kr 선거공약정보 API | ok (401, 키 없음) | **timeout** ×3 |
| 선관위 정책공약마당 (policy.nec.go.kr) | ok | ok |
| 경기도청 (www.gg.go.kr) | ok | **timeout** ×3 |
| 경기도 열린도지사실 공약 (pledges.view) | ok | **timeout** ×1 (추가 후 1회 측정) |
| 경기도 robots.txt | ok | **timeout** ×1 |
| 서울시청 (www.seoul.go.kr) | ok | ok |
| 서울시장 공약실천계획 (mayor.seoul.go.kr) | ok | ok ×1 |
| 서울 e-book 공약 목록 (ebook.seoul.go.kr) | ok | ok ×1 |
| 서울 정보소통광장 (opengov.seoul.go.kr) | ok | **timeout** ×3 |
| 한국매니페스토실천본부 | ok | ok |

`timeout`은 연결 자체가 응답 없이 끊기는 형태다(HTTP 오류 페이지가 아님). 해외 IP 대역을 방화벽에서 차단하는 경우로 보인다.
[adapter-survey.md](adapter-survey.md)의 WebFetch 결과(경기도 200)와는 다르다. 실제 배치 환경인 Actions 측정값을 기준으로 삼는다.

## 시사점

1. **선관위 API 수집은 국내에서 실행**한다. 선거 후 1회 적재라서 로컬 PC 실행으로 충분하다. 재수집을 자동화하려면 self-hosted runner가 필요하다.
2. **경기도 어댑터는 self-hosted runner(국내) 전용**이다. PROJECT.md 3.5의 "국내 IP 이슈 대응"을 적용한다. 워크플로에서 `runs-on: [self-hosted, kr]`로 분리한다.
3. **서울시 어댑터는 Actions에서 실행할 수 있다.** 대상인 mayor.seoul.go.kr와 ebook.seoul.go.kr 모두 해외에서 응답한다. 다만 ebook은 robots.txt가 전면 금지라서 원본 확보는 수동으로 한다([adapter-survey.md](adapter-survey.md) 4장).
4. 정보소통광장은 이행현황 출처가 아니므로 영향이 없다.
5. 프로브는 매월 1일에 자동으로 다시 돈다. 차단 정책이 바뀌면 결과 표(Actions job summary)로 확인한다.

## 재현

```bash
python scripts/probe_access.py --label local-kr
gh workflow run probe-kr-access.yml
```
