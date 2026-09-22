# 어댑터 사전 조사: 경기도·서울특별시 공약 이행현황 페이지 구조

- 조사일: 2026-09-22 (1주차 과제, PROJECT.md 체크리스트 "경기도·서울시 이행현황 페이지 구조 조사")
- 방법: WebSearch + WebFetch만 사용했고 브라우저 도구는 쓰지 않음. WebFetch 요청은 Anthropic 인프라(해외, 미국 추정)에서 나가므로 **해외 IP 접속 결과**로 간주함.
- 한계: WebFetch는 HTML을 마크다운으로 바꾼 뒤 요약해서 돌려줌. 그래서 `<script>` 내용, 이미지 alt, 동적으로 생성되는 href는 보이지 않음. 이런 이유로 확인하지 못한 항목에는 "미확인" 표시를 붙임.

---

## 0. 전제: 민선9기 전환 상황

제9회 전국동시지방선거는 2026-06-03에 치러졌고 당선자는 2026-07-01에 취임함.

| 지자체 | 민선8기 | 민선9기 (2026-07-01~) | 사이트 영향 |
| :- | :- | :- | :- |
| 경기도 | 295개 과제 | 단체장 교체 | 열린도지사실 사이트를 새로 만들면서 **민선8기 공약 페이지가 모두 사라짐(404)** |
| 서울시 | 245개 공약 | 단체장 연임 | 기존 시장실 사이트를 그대로 운영. 민선8기 자료는 계속 게시 중 |

> 인물명·정당명은 어댑터 설계와 무관하므로 적지 않는다(PROJECT.md 10장). 사이트 구조에 영향을 주는 "교체/연임" 여부만 기록한다.

출처: [제9회 전국동시지방선거 - 위키백과](https://ko.wikipedia.org/wiki/%EC%A0%9C9%ED%9A%8C_%EC%A0%84%EA%B5%AD%EB%8F%99%EC%8B%9C%EC%A7%80%EB%B0%A9%EC%84%A0%EA%B1%B0), [아주경제 2026-07-14](https://www.ajunews.com/view/20260714114946228)

---

## 1. 경기도

### 1.1 진입 URL

| URL | 오늘 상태 | 내용 |
| :- | :- | :- |
| https://www.gg.go.kr/governor/ | 200 | 민선9기 열린도지사실. 메뉴 "약속과 실천" |
| https://www.gg.go.kr/governor/user/promises/pledges.view | 200 | **"공약실천계획을 수립하고 있습니다"라는 안내만 있음.** 공약 목록, 상태, 첨부 모두 없음 |
| https://www.gg.go.kr/governor/user/promises/goals.view | 200 | 도정목표. 준비 중 |
| https://governor.gg.go.kr/promises/election-promise/ (민선8기 공약사항) | 301 → `https://www.gg.go.kr/governor/promises/election-promise/` → **404** | 소멸 |
| https://governor.gg.go.kr/promises/status/ (민선8기 공약추진현황) | 301 → `https://www.gg.go.kr/governor/promises/status/` → **404** | 소멸 |
| https://governor.gg.go.kr/promises/manifesto/ | 301 → **404** | 소멸 |
| 구 사이트의 다른 경로(예: `/policy/press/?mod=document&uid=14992`) | 301 → **404** | 구 사이트 전체가 사라진 것으로 판단 |

- pledges.view 안내문에 따르면 "경기도지사 공약관리 규정"에 실천계획을 **취임 후 6개월 이내**에 세우도록 되어 있음. 이 기한대로라면 민선9기 실천계획은 **2026-12-31 전후**에 공개될 것으로 예상함. 절차는 실천계획 작성, 검토·조정, 도민 의견수렴(도민배심원), 확정·공개 순.
- 민선8기 원자료를 대신할 수 있는 곳:
  - 제3자 사본: [경기시민사회 온라인 자료관 톺: 경기도 민선8기 공약실천계획서](https://gcsarchive.or.kr/kr/data/policy.php?bgu=view&idx=4326). 2023-07-04 게시, Google Drive 링크. 이행현황은 없고 실천계획서만 있음.
  - 경기도 전자책([ebook.gg.go.kr](https://ebook.gg.go.kr/home/index.php)): '공약'으로 검색하면 31건이 나오지만 모두 민선7기 이전(2017~2020) 자료임. 민선8기 추진현황은 없음.

### 1.2 형식, URL 패턴, 렌더링

- **민선9기 신규 사이트**: Java 계열 `.view` 경로(`/governor/user/{섹션}/{페이지}.view`)를 씀. 본문 텍스트가 HTML 안에 들어 있어 서버 렌더링으로 판단함. 공약 데이터 구조는 아직 없어서 목록/상세 패턴은 **미정**.
- **민선8기 구 사이트** (검색엔진 색인으로 추정): WordPress 기반에 **KBoard 게시판 플러그인**을 씀.
  - 공약추진현황 = `kboard_id=28`
  - 파라미터: `pageid`(페이지), `mod=list|document`, `uid`(게시물), `view_iframe=1`
  - 색인에 `pageid=24` URL이 있었음. 목록이 24페이지를 넘었다는 뜻이므로 과제별 게시물 구조였을 가능성이 있음.
  - 상단에 상태별 집계가 있었고, 공약실천계획서가 기준일별(2025.6.30 기준, 2025.12.31 기준)로 게시되어 있었음(검색 스니펫 기준).
- **경기도 본청 공통 패턴** (다른 게시판 참고용):
  - 목록: `/bbs/board.do?bsIdx=&menuId=`
  - 상세: `/bbs/boardView.do?bsIdx=&bIdx=&menuId=&page=`
  - 첨부: `/cmmn/download.do?idx=`
  - 콘텐츠: `/contents/contents.do?ciIdx=&menuId=`

### 1.3 과제 필드와 상태값

- 규모: 3대 비전, 9대 분야, **295개 실천과제**. 총 38조4,418억 원(국비 5조166억, 도비 8조865억). 2023-01 확정. 출처: [경기도뉴스포털 2023-01-09](https://gnews.gg.go.kr/news/news_detail.do?number=202301091035161657C048&s_code=C048)
- **상태값 원문 어휘** (민선8기 열린도지사실 공약추진현황. 원 페이지가 사라져서 검색엔진 스니펫으로만 확인함):

| raw 상태값 | 집계(최종 확인분) | 정의 요약 |
| :- | -: | :- |
| `완료` | 62 | 이행 완료 |
| `이행 후 계속추진` | 207 | 이행한 뒤 추가 목표를 세우거나 반복해서 추진 |
| `정상추진` | 23 | 임기 안에 완료 예상 |
| `일부추진` | 0 | 목표 대비 부진 |
| `보류` | 0 | 추진 보류 |
| `폐기` | 3 | 여건상 폐기 |

  - 경기도는 `이행 후 계속추진`처럼 **띄어쓰기가 있는 표기**를 쓴 것으로 보임. 매니페스토 표준 표기는 `이행후계속추진`. 매핑할 때 공백을 제거하는 정규화가 필요함.
- 과제 단위 필드(과제명, 담당부서, 과제별 예산, 진척률, 추진실적 텍스트)는 원 페이지가 없어져 **미확인**. 공약실천계획서 사본(PDF)으로 확인해야 함.
- 매니페스토실천본부 연례 평가(2026년 발표, 2025년 12월 기준)가 존재함 → 교차검증(3.2) 대상. 등급·수치는 PDF 확보 후 검수 절차로만 적재한다.

### 1.4 갱신 주기와 최신 시점

- 2023-01 보도자료는 "분기별로 공약사업 이행점검"을 한다고 밝힘. 이건 **내부 점검 주기**임.
- 공개 자료는 기준일이 6/30과 12/31인 **반기 단위**로 보임. 확인된 최신 기준일은 **2025-12-31**임. 2026년 상반기분이 게시됐는지는 사이트가 사라져서 확인 불가.
- 민선9기: 2026-12 전후에 실천계획이 공개되고, 그 다음 추진현황 공개 주기가 정해질 것.

### 1.5 robots.txt

`https://www.gg.go.kr/robots.txt` (200):

```
User-agent: *
Allow:/site/gg/common/img/
Disallow: /common/
Disallow: /include/
Disallow: /site/
Disallow: /template/
Disallow: /down/
Disallow: /ubhome/
Disallow: /*.xml$
Disallow: /welfare/
Allow:/sitemap.xml

Sitemap: https://www.gg.go.kr/sitemap.xml
```

- `/governor/`, `/bbs/`, `/cmmn/download.do`는 Disallow 대상이 아니므로 **허용**됨. `/down/`, `/site/`는 금지.
- `https://governor.gg.go.kr/robots.txt`는 301로 `https://www.gg.go.kr/governor/robots.txt`로 넘어가고 거기서 404가 남. 호스트가 통합되어 www.gg.go.kr 루트 규칙이 적용됨.
- `https://ebook.gg.go.kr/robots.txt`는 302로 `/404.html`로 넘어감. 파일이 없다는 뜻. 첫 시도에서는 "Socket is closed"가 나왔음.
- `https://data.gg.go.kr/robots.txt`는 404.

### 1.6 공공누리(KOGL)

- 신규 열린도지사실(pledges.view)과 본청 게시판 페이지에서 "공공누리/KOGL/제n유형" 문자열이 **검출되지 않음**. 푸터에는 `©GYEONGGI PROVINCE All Rights Reserved`만 있음.
- WebFetch가 이미지 alt 텍스트를 빼먹었을 수 있음. 게시물이나 첨부에 붙은 공공누리 배지는 **미확인**.
- 구 사이트 첨부의 유형은 사이트가 사라져서 확인할 수 없음.

### 1.7 해외 접속 결과

| 요청 | 결과 |
| :- | :- |
| www.gg.go.kr (robots, /governor/, /governor/user/promises/*.view, /opendata/, /bbs/, sitemap.xml) | 모두 200. 차단이나 캡차 없음 |
| governor.gg.go.kr/* | 301 → www.gg.go.kr/governor/* (구 경로는 404) |
| ebook.gg.go.kr | 메인·목록 200 (EUC-KR). robots.txt 1차 "Socket is closed", 2차 302 |
| data.gg.go.kr | 200. 검색 결과는 JS로 로딩돼서 HTML에는 0건으로 보임 |
| webarchives.pa.go.kr (국가기록원 웹아카이브) | **ECONNREFUSED 152.99.238.213:443**. 해외 차단일 가능성 |

### 1.8 오픈데이터와 API

- **data.go.kr**: '경기도 공약' 검색 10건, '공약이행' 검색 17건 가운데 **경기도 본청이 제공하는 공약 추진현황 데이터셋은 없음**. 본청 자료는 '민선6기 메시지 모음집', '연정의 바람' PDF뿐임. 시군 단위(연천군, 수원시, 하남시)는 CSV/JSON 데이터가 있음. [검색](https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword=%EA%B2%BD%EA%B8%B0%EB%8F%84+%EA%B3%B5%EC%95%BD)
- **경기데이터드림**: 통합검색이 JS로 로딩돼 WebFetch로는 0건으로 보임. `site:data.gg.go.kr 공약`으로 웹검색해도 관련 데이터셋이 없음. 수동 확인이 필요함.
- 결론: **크롤링을 대신할 공개 데이터셋은 없음.**

---

## 2. 서울특별시

### 2.1 진입 URL

| URL | 상태 | 내용 |
| :- | :- | :- |
| https://mayor.seoul.go.kr/oh/seoul/manifesto.do | 200 | "공약실천계획" 페이지. 민선8기 e-book 3종 링크와 **공약 변경 내역 표**(2024년 24건, 2025년 25건) |
| https://ebook.seoul.go.kr/Viewer/VHTWPIURJTKI | 200 | 민선8기 공약실천계획서 (2023-04-28 등록). 검색 결과에 같은 제목이 `/Viewer/IO6DPZQQIREV`로도 있음 |
| https://ebook.seoul.go.kr/Viewer/manifesto202606 (= `/Viewer/JU7AQQ000YY3`) | 200 | **민선8기 서울특별시장 공약이행현황(2026년 6월 말 기준)**, 2026-08-05 등록. 민선8기 최종본 |
| https://ebook.seoul.go.kr/Viewer/MUG73V6XLXBF | 200 | 시민공약평가단 운영결과보고서 |
| https://ebook.seoul.go.kr/library/list_content.php?class=31&order=title&n=7 | 200 | e-book 분류 '공약/연설문' 목록 (`n`=페이지) |

공약이행현황 e-book 이력(시계열 백필용):

| 기준 시점 | 등록일 | Viewer ID |
| :- | :- | :- |
| 2023년 6월 말 | 2023-08-25 | `1AC7AZCBBXVB` |
| 2023년 12월 말 | 2024-02-07 | `BWDR06UHQNLR` |
| 2024년 6월 말 | 2024-08-08 | `BAWGFLTGSHE2` |
| 2024년 12월 말 | 2025-02-13 | `7L8GA6445BIF` |
| 2025년 6월 말 | 2025-09-02 | `I6L4ZW6RU5UA` |
| 2025년 12월 말 | 2026-02-20 | 미확인 (검색 스니펫으로만 확인) |
| 2026년 6월 말 | 2026-08-05 | `JU7AQQ000YY3` (별칭 `manifesto202606`) |

- 같은 목록에 "제38대 서울특별시장 공약실천계획서"(`/Viewer/78YQOV0X9J13`, 2021 보궐 임기분)와 민선7기 이전 자료도 있음.
- **민선9기**: 재선 뒤에도 manifesto.do에는 민선9기 언급이 없음. 보도에 따르면 'G3 서울플랜' 종합계획을 2026년 9월에 발표할 구상임. 민선9기 공약실천계획서가 언제 나올지는 미정. 출처: [서울신문 2026-06-29](https://www.seoul.co.kr/news/society/2026/06/29/20260629500121)
- **정보소통광장**: 공약 전용 메뉴가 없음(`/mayor`는 404). 결재문서로 관련 문서가 드문드문 있음(예: [민선8기 공약실천 전략보고회 결과 보고](https://opengov.seoul.go.kr/sanction/26425297)). 추진현황 데이터 출처로는 적합하지 않음.

### 2.2 형식, URL 패턴, 렌더링

- **공약이행현황 본문은 e-book 뷰어(JS `viewer2`) 안에만 있음.**
  - HTML에는 본문 텍스트가 없음. 페이지는 이미지나 JS로 렌더링됨.
  - "원본파일 다운로드" 버튼은 있지만 href가 정적 HTML에 없음. JS로 생성되는 것으로 보임.
  - 원본 파일 형식(PDF 추정)과 다운로드 URL 패턴은 **미확인**.
- manifesto.do의 **공약 변경 내역 표는 서버 렌더링 HTML**임.
  - 컬럼: `연번`, `공약번호`, `공약명`, `변경내용(전/후)`, `변경사유`, `변경시기`
  - 공약번호 형식 예: `1-8`, `2-1`, `3-13`
  - 섹션은 앵커(`#cont1`, `#cont2`)로 이동하고 쿼리 파라미터는 없음.
- e-book 목록 페이지는 서버 렌더링이며 `?class=31&order=title&n={page}` 형태임.

### 2.3 과제 필드와 상태값

- 규모:
  - 실천계획서 기준 244개 (상생도시 56, 글로벌선도도시 68, 안심도시 69, 미래감성도시 51. 웹검색 요약 기준)
  - 이행현황 기준 245개 (변경을 반영한 것으로 추정)
- **확인된 상태값**: `완료` 191건, `정상추진` 54건. 부진이나 불이행은 0건. 이 수치는 2차 인용이고 기준 시점은 미상임. 원 게시글(sasw.or.kr)은 403이 떠서 원문을 확인하지 못함.
- 상태 어휘 전체 목록, 그리고 과제별 필드(담당부서, 예산, 진척률, 추진실적 텍스트)는 **미확인**. 원본 파일을 확보해야 알 수 있음. 매니페스토 표준 6분류(완료/이행후계속추진/정상추진/일부추진/보류/폐기)를 쓸 가능성이 높음.

### 2.4 갱신 주기와 최신 시점

- **반기**: 6월 말과 12월 말 기준. 기준일로부터 약 1.5~2.5개월 뒤에 e-book으로 게시됨(위 이력표 참조).
- 근거: 「서울특별시 시장공약 관리 규칙」 제7조. 주관부서가 반기별로 자체 점검하고, 총괄부서가 연 2회 홈페이지에 공개하도록 되어 있음. 2017-02-23 시행본 기준이며 최신 개정 여부는 미확인. 출처: [U-LEX](https://www.ulex.co.kr/%EB%B2%95%EB%A5%A0/1278646-2016696-%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C%EC%8B%9C%EC%9E%A5%EA%B3%B5%EC%95%BD)
- **최신: 2026년 6월 말 기준**(2026-08-05 등록). 민선8기 마지막 보고서임.

### 2.5 robots.txt

`https://mayor.seoul.go.kr/robots.txt` (200):

```
User-agent: *
Disallow: /

Allow: /$
Allow: /robots.txt$
Allow: /index.html$
Allow: /sitemap.xml
Allow: /index.do
Allow: /oh/

Sitemap: https://mayor.seoul.go.kr/sitemap.xml
```

manifesto.do는 `/oh/` 아래에 있어서 **허용**됨.

`https://ebook.seoul.go.kr/robots.txt` (200):

```
user-agent: *
disallow: /
```

**e-book 전체가 크롤링 금지임.** 이행현황 원본을 자동으로 수집하는 데 가장 큰 걸림돌.

`https://www.seoul.go.kr/robots.txt` (200):
- 기본 `Disallow: /`
- 허용 목록: `/main`, `/seoul`, `/news`, `/helper`, `/citizen`, `/service`, `/policy` 등

`https://opengov.seoul.go.kr/robots.txt` (200):
- 금지: `/og/com/`, `/out/`, `/search`
- 허용: `/sanction`, `/policy`, `/research`, `/press`, `/data`, `/budget` 등 대부분

`https://data.seoul.go.kr/robots.txt` (200): `Allow: /`

### 2.6 공공누리(KOGL)

- manifesto.do와 e-book 뷰어에서 **공공누리 표기가 검출되지 않음**. 푸터는 `© Seoul Metropolitan Government all rights reserved.`
- [서울시 저작권 정책](https://www.seoul.go.kr/helper/copyright.do):
  - 공공누리 유형은 저작물마다 표시에 따라 다름.
  - **공공누리가 붙지 않은 자료는 담당자와 사전에 협의한 뒤 이용**하라는 취지임.
  - WebFetch 요약에는 사이트 자체가 제4유형이라는 언급이 있었으나 재확인이 필요함.
- [정보소통광장 저작권정책](https://opengov.seoul.go.kr/copyright): 개별 CCL/KOGL 배지를 확인하라고 하며, 배지가 없으면 허락을 받아야 함.

### 2.7 해외 접속 결과

| 요청 | 결과 |
| :- | :- |
| mayor.seoul.go.kr (robots, manifesto.do) | 200 |
| ebook.seoul.go.kr (robots, Viewer 3건, list 2페이지) | 200. 뷰어는 셸만 받아짐. 원본 파일은 시도하지 않음(URL 미상, robots 금지) |
| www.seoul.go.kr (robots, copyright.do) | 200 |
| opengov.seoul.go.kr (robots, copyright) | 200. `/mayor`는 404 |
| data.seoul.go.kr (robots, 목록) | 200. `searchKeyword` GET 파라미터가 적용되지 않음 |

차단, 캡차, 지연은 없었음.

### 2.8 오픈데이터와 API

- **data.go.kr**: '서울특별시 공약' 검색 2건이 모두 자치구 데이터임(광진구 `15036478`, 서초구 `15142594`). **서울시 본청의 시장 공약 데이터셋은 없음.**
- **서울 열린데이터광장**: `site:` 웹검색 결과에 공약 데이터셋이 없음(시민참여예산 등만 나옴). 사이트 내 검색은 수동 확인이 필요함.
- 결론: **크롤링을 대신할 공개 데이터셋은 없음.**

---

## 3. 비교표

| 항목 | 경기도 | 서울특별시 |
| :- | :- | :- |
| 민선9기 단체장 | 교체 | 연임 |
| 최적 진입 URL | https://www.gg.go.kr/governor/user/promises/pledges.view (현재 안내문만) | https://mayor.seoul.go.kr/oh/seoul/manifesto.do → e-book |
| 민선8기 자료 현황 | **원 사이트 소멸(404)**. 제3자 사본은 실천계획서뿐 | e-book으로 계속 게시 중 (2023.6~2026.6, 7회분) |
| 민선9기 공개 | 미게시. 규정상 2026-12 전후 | 미게시. 시점 미정 |
| 형식 | (8기) WordPress KBoard HTML 게시판 + 기준일별 첨부 / (9기) 미정 | e-book 뷰어(JS) + 원본파일(PDF 추정) |
| 목록 URL 패턴 | (9기) `/governor/user/promises/*.view` | `ebook.seoul.go.kr/library/list_content.php?class=31&n=` |
| 렌더링 | 서버 렌더링 | 목록은 서버 렌더링, 본문은 JS 뷰어 |
| 상태 어휘 | 완료 / 이행 후 계속추진 / 정상추진 / 일부추진 / 보류 / 폐기 | 완료 / 정상추진 확인. 전체 어휘는 미확인 |
| 공개 주기 | 공개는 반기(6/30, 12/31), 내부 점검은 분기 | 반기(6월 말, 12월 말) + 약 2개월 지연 |
| 최신 기준 시점 | 2025-12-31 (확인분) | 2026-06-30 |
| robots.txt | `/governor/`, `/bbs/`, `/cmmn/download.do` 허용 | manifesto.do 허용, **ebook 전면 금지** |
| 공공누리 | 미검출(미확인) | 미검출. 저작권정책상 미부착 자료는 사전 협의 |
| 해외 IP (WebFetch) | 정상(200/301/404). 국가기록원 웹아카이브는 ECONNREFUSED | 정상(200) |
| 해외 IP (**GitHub Actions 실측**) | **www.gg.go.kr 타임아웃 (2회 재현)** | www.seoul.go.kr 정상, opengov.seoul.go.kr 타임아웃 — [access-probe.md](access-probe.md) |
| 오픈데이터 대체재 | 없음 | 없음 |

---

## 4. 어댑터 설계 시사점

1. **PROJECT.md의 전제를 고쳐야 함.** 6장 데이터 소스 레지스트리의 "경기도 분기별 추진현황 크롤링"과 "서울시 분기"는 현실과 맞지 않음.
   - 경기도: 원천 페이지가 사라졌고, 민선9기 데이터는 2026-12 전후까지 없음.
   - 서울시: 반기 단위 문서임.
   - 따라서 `task_snapshots.period`를 분기 고정으로 두지 말고 **기준일(date)**로 저장하는 편이 안전함. 반기, 분기, 비정기가 섞여도 처리할 수 있음.
2. **어댑터 인터페이스를 단계별로 나누기**: `discover()`(문서 목록과 기준시점 탐지) → `acquire()`(원본 확보. `auto`/`manual` 모드) → `parse()`(HTML/PDF/HWP) → `normalize()`.
   - 서울은 `discover`를 robots가 허용하는 manifesto.do와 e-book 목록으로 할 수 있음. 다만 목록 도메인도 robots 금지이므로, 실제로는 manifesto.do의 링크만 쓰는 편이 가장 안전함.
   - `acquire`는 robots에 막히므로 **수동 모드**로 둠. 연 2회라 사람이 원본파일을 내려받아 레포 `raw/`(또는 스토리지)에 올리고 워크플로를 수동 트리거하는 비용이 작음.
3. **서울시에 정식 경로를 문의하기**: 서울시(공약 총괄: 시장공약 관리 규칙상 기획담당관. 민선9기에는 조직이 바뀌었을 수 있음)에 원본 파일 제공이나 e-book 크롤링 허용을 요청함. 병행해서 data.go.kr '공공데이터 제공신청'(공공데이터법 제27조)으로 CSV 개방을 요청함. 개방되면 가장 좋음.
4. **경기도 민선8기 백필은 일회성 import 어댑터로 따로 두기**. 확보 경로 후보:
   - 경기도 정보공개청구: 2025.12.31 및 2026.6.30 기준 추진현황 원본(xlsx/hwp)
   - 경기도의회 행정사무감사·업무보고 첨부
   - 제3자 사본
   - 이렇게 모은 데이터는 주기적 크롤러와 분리해 `adapter_id = gg-8th-archive`처럼 관리함.
5. **경기도 민선9기는 워처(watcher)부터 만들기**: pledges.view 본문 해시를 주 1회 비교하고, "수립하고 있습니다" 문구가 사라지면 Discord 알림을 보냄. 실제 파서는 게시 형식을 확인한 뒤에 작성함(새 사이트는 서버 렌더링이라 HTML 파싱 난이도는 낮을 것으로 예상).
6. **상태값 정규화**:
   - raw는 그대로 보존하고, 공백을 제거한 키(`이행후계속추진`)로 매핑함.
   - PROJECT.md의 5분류는 `보류·폐기`를 합쳐 두었지만 raw 수준에서는 **보류와 폐기를 따로 보존**해야 함. 경기도 폐기 3건처럼 의미가 다름.
7. **민선9기 공약 원문은 선관위 API로 먼저 확보하기**: 선관위 선거공약 API(data.go.kr 15040587, 시도지사 포함)로 공약 목록을 먼저 채움. 지자체 실천계획이 나오면 공약↔과제 매칭을 붙임. 두 지자체 모두 실천계획이 없는 공백기(~2026-12)에도 서비스를 할 수 있게 됨.
8. **라이선스(DATA_LICENSE.md와 연계)**: 두 곳 모두 공공누리 표기가 확인되지 않음.
   - 과제명, 상태값, 수치 같은 사실 데이터만 정규화해 저장·표시함.
   - 추진실적 텍스트는 **짧게 발췌하고 원문 링크를 붙이는 방식**으로 제한함.
   - `evidence_chunks`의 원문 재배포는 기본적으로 끔.
   - 저작권법 제24조의2(공공저작물 자유이용)가 적용되는지는 법률 검토가 필요함. 서울시 저작권정책의 "미부착 시 사전 협의"와 충돌할 수 있음.
9. **해외 IP**: ~~gg.go.kr, seoul.go.kr 계열은 모두 정상 응답해서 GitHub Actions로 실행해도 됨.~~ → **정정(2026-09-22)**: WebFetch 출구와 GitHub Actions 러너(미국, Azure)의 결과가 다름. Actions 실측에서 `www.gg.go.kr`, `apis.data.go.kr`, `opengov.seoul.go.kr`는 타임아웃(2회 재현), 국내 PC에서는 모두 정상. 경기도 어댑터와 선관위 API 수집은 **국내 실행 환경(self-hosted runner)**이 필요함. 자세한 결과는 [access-probe.md](access-probe.md). 아래 대상을 `scripts/probe_targets.json`에 추가해 계속 측정함:
   - `https://www.gg.go.kr/governor/user/promises/pledges.view`
   - `https://mayor.seoul.go.kr/oh/seoul/manifesto.do`
   - `https://ebook.seoul.go.kr/library/list_content.php?class=31&order=title&n=7`
   - `https://governor.gg.go.kr/promises/status/` (404 회귀 확인용)
10. **인코딩 주의**: ebook.gg.go.kr은 EUC-KR임. 검색어는 `%B0%F8%BE%E0`(공약)처럼 EUC-KR로 퍼센트 인코딩해야 결과가 나옴.

---

## 5. 미확인 및 후속 확인 필요

- [ ] **서울 e-book "원본파일 다운로드"의 실제 URL과 파일 형식**(PDF/HWP), 로그인 필요 여부, 해외 IP에서 받을 수 있는지. 국내에서 브라우저 개발자도구 네트워크 탭으로 확인할 것. robots 금지이므로 자동화 여부는 서울시 답변을 받은 뒤 결정.
- [ ] 서울 공약이행현황의 **과제별 필드와 상태 어휘 전체 목록**. 2026년 6월 말 기준본 원본을 확보해 확인.
- [ ] 서울 "2025년 12월 말 기준" e-book의 Viewer ID.
- [ ] 서울 민선8기 공약 수(244 vs 245)와 "완료 191 / 정상추진 54"의 기준 시점. 원본으로 대조.
- [ ] 서울 민선9기 공약실천계획서 공개 시점과 형식. G3 서울플랜(2026-09 예정)과 연계되는지.
- [ ] 「서울특별시 시장공약 관리 규칙」 최신 개정본 (elis.go.kr). law.go.kr은 JS로 렌더링돼 WebFetch로 본문을 받지 못함.
- [ ] 「경기도지사 공약관리 규정」 원문: 공개 주기, 상태 정의, 수립 기한 6개월.
- [ ] 경기도 민선8기 추진현황 원자료(2025.12.31 기준, 2026년 상반기분이 있다면 그것까지) 확보. 정보공개청구, 경기도의회 자료, 경기도기록원, 국가기록원 웹아카이브를 국내 IP로 재시도.
- [ ] 경기도 민선8기 구 사이트의 과제 단위 필드(담당부서, 예산, 진척률, 추진실적) 구조. 사이트가 사라져 복원이 불가하면 실천계획서 PDF로 대체.
- [ ] **공공누리 유형**: 경기도 게시물·첨부의 배지, 서울시 e-book 원본 파일 내 표기. 브라우저로 이미지 alt와 푸터를 직접 확인. 서울시 사이트가 "제4유형"이라는 요약도 재확인.
- [ ] 경기데이터드림과 서울 열린데이터광장의 사이트 내 검색 결과를 수동으로 확인(JS 로딩과 파라미터 미적용 때문에 WebFetch로 확인 불가).
- [ ] WebFetch 출구 IP의 국가가 확정되지 않았음. GitHub Actions에서 `scripts/probe_access.py`로 위 대상을 재측정해 실제 배치 환경 기준으로 기록할 것.
- [ ] 국가기록원 웹아카이브(webarchives.pa.go.kr)의 ECONNREFUSED가 해외 차단인지 일시 장애인지 국내 IP로 비교.

---

## 참고 출처

- 경기도 열린도지사실(민선9기): https://www.gg.go.kr/governor/ , https://www.gg.go.kr/governor/user/promises/pledges.view
- 경기도 robots.txt: https://www.gg.go.kr/robots.txt
- 경기도 민선8기 공약 확정 보도: https://gnews.gg.go.kr/news/news_detail.do?number=202301091035161657C048&s_code=C048
- 경기도 공약실천계획서 제3자 사본: https://gcsarchive.or.kr/kr/data/policy.php?bgu=view&idx=4326
- 경기도 전자책: https://ebook.gg.go.kr/home/index.php
- 매니페스토 평가 보도: https://www.mt.co.kr/policy/2026/04/02/2026040209272822383 , https://www.news2day.co.kr/article/20260525500053
- 서울시장 공약실천계획: https://mayor.seoul.go.kr/oh/seoul/manifesto.do
- 서울 e-book 목록: https://ebook.seoul.go.kr/library/list_content.php?class=31&order=title&n=7
- 서울 공약이행현황(2026.6 말): https://ebook.seoul.go.kr/Viewer/manifesto202606
- robots.txt: https://mayor.seoul.go.kr/robots.txt , https://ebook.seoul.go.kr/robots.txt , https://www.seoul.go.kr/robots.txt , https://opengov.seoul.go.kr/robots.txt , https://data.seoul.go.kr/robots.txt
- 저작권정책: https://www.seoul.go.kr/helper/copyright.do , https://opengov.seoul.go.kr/copyright
- 서울특별시 시장공약 관리 규칙: https://www.ulex.co.kr/%EB%B2%95%EB%A5%A0/1278646-2016696-%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C%EC%8B%9C%EC%9E%A5%EA%B3%B5%EC%95%BD
- data.go.kr 검색: https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword=%EA%B3%B5%EC%95%BD%EC%9D%B4%ED%96%89
- 선거 결과: https://ko.wikipedia.org/wiki/%EC%A0%9C9%ED%9A%8C_%EC%A0%84%EA%B5%AD%EB%8F%99%EC%8B%9C%EC%A7%80%EB%B0%A9%EC%84%A0%EA%B1%B0
