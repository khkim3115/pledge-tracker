# 중앙선관위(NEC) Open API 검증 노트 — 선거공약 / 당선인 / 코드정보

조사일: 2026-09-22. 확인 근거는 세 가지다: (1) data.go.kr 상세 페이지, (2) 공식 활용가이드 hwpx(data.go.kr 첨부 zip), (3) 이 API를 실제로 호출하는 공개 GitHub 코드와 그 코드가 커밋한 수집 결과물.
표기: **확인** = 공식 문서나 실호출 결과로 확인됨 / **간접 확인** = 제3자 실사용 코드·데이터로만 확인됨 / **미확인** = 확인하지 못함.
이번 조사에서는 유효한 serviceKey로 직접 호출하지 않았다. 키 없이 보낸 호출과 잘못된 키로 보낸 호출의 게이트웨이 오류 응답만 직접 관찰했다.

---

## 0. 공통 사항

| 항목 | 내용 | 상태 |
|---|---|---|
| 호스트 | `http://apis.data.go.kr/9760000/...` (가이드 표기). data.go.kr 페이지는 `https://`로 표기하며, 둘 다 실사용 중이다. | 확인 |
| 인증 파라미터 | 가이드 표기는 `serviceKey`, data.go.kr 페이지 표기는 `ServiceKey`. 게이트웨이는 둘 다 인식한다. 잘못된 키를 두 이름으로 보내면 모두 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`가 오고, 키를 빼면 `SERVICE_KEY_IS_NULL`이 온다. | 확인(직접 관찰) |
| 데이터 포맷 | `resultType=json` 또는 `xml`. 생략하면 **xml**이다. `_type=json`과 `type=json`은 동작하지 않는다는 실사용 보고가 있다. | 확인(가이드) / 간접 확인 |
| 페이지 | `pageNo`(최대 100000), `numOfRows`(**최대 100**. 100보다 크게 요청해도 100으로 잘린다는 보고가 있다) | 확인(가이드) / 간접 확인 |
| 성능 한도 | 초당 30tps(가이드). 개발계정은 API마다 일 10,000건이며, 운영계정은 활용사례를 등록하면 증설할 수 있다. 활용신청은 API별로 따로 하고 자동승인된다. | 확인 |
| 데이터 갱신 | 선거공약·당선인: "매 선거 종료 후 두 달 이내". 코드정보: "매 선거 예비후보자 등록일 이후". | 확인(가이드) |

### serviceKey: Encoding 키와 Decoding 키
- data.go.kr는 같은 키를 Encoding 형태와 Decoding 형태 두 가지로 준다. 어느 쪽을 쓸지는 호출 방식에 달렸다.
  - **파이썬 `requests.get(url, params={...})`처럼 라이브러리가 쿼리를 인코딩해 주는 경우에는 Decoding 키를 쓴다.** Encoding 키를 넣으면 이중 인코딩되어 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`가 난다.
  - URL 문자열을 직접 이어 붙이는 경우에는 Encoding 키를 쓴다.
  - 실사용 예: `unquote(key)` 후 params에 넣는다(minskapo/nec-2026-pledges). R httr는 `DATA_GO_DECODE_KEY`를 쓴다(bit2r). URL을 수동으로 조립할 때는 `NEC_API_KEY_ENCODED`를 쓴다(imurodl/api-test).
- 권장: `.env`에는 Decoding 키를 두고, 코드에서 `urllib.parse.unquote()`를 한 번 적용한다. 이렇게 하면 어느 형태의 키를 넣어도 안전하다.

### 응답 봉투(envelope)
**XML**: 가이드 예제와 실호출 fixture가 일치한다. 확인.
```xml
<response>
  <header><resultCode>INFO-00</resultCode><resultMsg>NORMAL SERVICE</resultMsg></header>
  <body>
    <items><item>...</item><item>...</item></items>
    <numOfRows>10</numOfRows><pageNo>1</pageNo><totalCount>3</totalCount>
  </body>
</response>
```
**JSON (`resultType=json`)**: 현행 형식은 `response.header` / `response.body.items.item` / `response.body.totalCount`이다. 간접 확인.
```json
{"response": {"header": {"resultCode": "INFO-00", "resultMsg": "NORMAL SERVICE"},
              "body": {"items": {"item": [ {...} ]}, "numOfRows": 10, "pageNo": 1, "totalCount": 1}}}
```
- 근거: bit2r/gpt-ds 교재(2024-03 렌더링)가 `response_list$response$body$items$item`으로 실데이터를 출력한다. SmileJune/before-you-vote(2026-05)와 kimbomi0603/kimbomi-site(2026-09)의 코드도 모두 `response.body.items.item`을 읽는다.
- ⚠ **구형 형식**: 2023-09 bit2r/map_challenge 출력은 루트가 오퍼레이션명이고 body/items 층이 없었다. 예: `{"getWinnerInfoInqire": {"header":…, "item":[…], …}}`. 그 사이에 형식이 바뀐 것으로 보인다. 파서는 두 형식을 모두 처리하도록 방어적으로 짜는 것이 좋다.
- **단건 응답일 때 `item`의 타입**: bit2r 2024 출력에서는 단건(1명) 응답에 `dplyr::select()`가 정상 동작했으므로 배열로 온 것으로 보인다. 간접 확인. 다만 공식 문서에는 명시가 없으므로 **list인지 dict인지 모두 정규화**해야 한다. 미확인.
- 값의 타입(숫자가 문자열로 오는지 여부): 구형(2023) 출력에서는 모든 필드가 문자열이었다. 현행 형식은 **미확인**이므로 `str()`로 정규화하는 것을 권장한다.
- 데이터가 없을 때(INFO-03) JSON의 body 모양(`items`가 빈 문자열인지, 필드가 아예 없는지 등): **미확인**.

### 결과 코드와 오류
| 층 | 형태 | 코드 |
|---|---|---|
| NEC 정상 | `header.resultCode` | **`INFO-00`** / `NORMAL SERVICE`. 가이드의 선거코드 예제에는 `00`으로 적혀 있으므로 `INFO-00`과 `00`을 모두 성공으로 처리한다. |
| NEC 데이터 없음 | `header.resultCode` | 실측값은 **`INFO-03`**이다. 해당 선거·후보의 데이터가 없을 때, 이미 삭제된 낙선자 공약, 2014년 이전 공약 등이 여기에 해당한다(k-vote-cli, polis-korea, SmileJune). 가이드 오류표에는 `ERROR-03`("데이터가 정보가 없습니다")로 적혀 있어 **둘 다 "빈 결과"로 처리**한다. INFO-03일 때의 resultMsg 문구는 미확인. |
| NEC 제공기관 오류(가이드) | `<response><header><resultCode>ERROR-xxx</resultCode>…` | `ERROR-301` 파일타입 누락 또는 유효하지 않음, `ERROR-310` 서비스 없음, `ERROR-333` 요청위치 값 타입 오류, `ERROR-340` 필수 파라미터 누락, `ERROR-500` 서버 오류, `ERROR-601` SQL 오류 |
| data.go.kr 게이트웨이 | `OpenAPI_ServiceResponse.cmmMsgHeader.{errMsg, returnAuthMsg, returnReasonCode}` | 직접 관찰한 결과: 키가 없으면 **HTTP 401**, `SERVICE_KEY_IS_NULL`, code `20`. 등록되지 않은 키는 **HTTP 403**, `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`, code `30`. `resultType=json`이면 JSON으로, 없으면 XML로 온다. 그 밖의 코드: 01 APPLICATION_ERROR, 04 HTTP_ERROR, 05 SERVICETIMEOUT, 10 INVALID_REQUEST_PARAMETER, 12 NO_OPENAPI_SERVICE, 20 SERVICE_ACCESS_DENIED/PERMISSION_DENIED, 22 일일 한도 초과, 23 초당 한도 초과, 29 BLACKLIST_IP, 31 활용기간 만료 |
| NEC 서버 오류 | HTTP 502/504 | 간헐적으로 발생하므로 재시도가 필요하다. 특정 레코드는 재현성 있게 502가 난다. 예: 9회 대구 교육감 `100162500`, 경남 교육감 `100153751`(2026-08-04 polis-korea). |

---

## 1. 선거공약정보 — `ElecPrmsInfoInqireService` (data.go.kr 15040587)

- 엔드포인트: `http://apis.data.go.kr/9760000/ElecPrmsInfoInqireService/getCnddtElecPrmsInfoInqire`. 확인.
- 오퍼레이션은 `getCnddtElecPrmsInfoInqire`(후보자 선거공약 정보 조회) 하나뿐이다. 확인.
- 가이드 버전은 v2.15(2025-02-12), data.go.kr 페이지 수정일은 2025-09-03.

### 요청
| 파라미터 | 필수 | 비고 |
|---|---|---|
| `serviceKey` | ✅ | |
| `pageNo` | – | |
| `numOfRows` | – | 최대 100. 후보 1명당 item 1건이다. |
| `resultType` | – | `xml`(기본) 또는 `json` |
| `sgId` | ✅ | 예: `20220601` |
| `sgTypecode` | ✅ | **1 대통령, 3 시·도지사, 4 구·시·군의 장, 11 교육감**만 해당한다(나머지 선거는 공약서를 제출하지 않는다). 확인(가이드와 페이지). 교육감(11)은 실제로 수집된다: 2026년 교육감 58명 전원의 5대 공약(15678910/budget), 2022년 당선인 17명(polis-korea). minskapo 코드의 "교육감 미지원" 주석은 틀렸다. |
| `cnddtId` | ✅ | = 후보자 API 또는 당선인 API의 **`huboid`**. 가이드 원문: "후보자ID 항목은 '후보자 정보 조회서비스' 또는 '당선인 정보 조회서비스'를 통해 확인 가능(huboid)". 확인. |

### 응답 item 필드 (철자는 그대로 옮김)
`num`, `sgId`, `sgTypecode`, `cnddtId`, `sggName`, `sidoName`, `wiwName`, `partyName`, `krName`, `cnName`, `prmsCnt`, 그리고 i = 1..10에 대해 `prmsOrd{i}`, `prmsRealmName{i}`, `prmsTitle{i}`, **공약 내용 필드**.

- ⚠ **공약 내용 필드 이름: 문서에는 `prmsCont{i}`로 되어 있지만 실제 응답은 `prmmCont{i}`이다.**
  - 문서 쪽 근거: data.go.kr 페이지, NEC 개방포털, 가이드 v2.15의 명세와 XML 예제가 모두 `prmsCont1`~`prmsCont10`이다.
  - 실제 응답 쪽 근거: 2021년 cow-coding/V.O.T.E의 DataFrame 출력 컬럼이 `prmmCont1`이다. polis-korea는 "문서상 prmsCont{i}이나 실제 응답은 prmmCont{i}"라고 명시했고, 2026년 데이터 3,330건의 본문을 이 필드로 수집했다. 15678910/budget은 2026년 교육감 290건 전부를 `prmmCont`로 채웠다. SmileJune도 2026년 응답에서 `prmmContN`을 확인했다.
  - → 수집기는 **`prmmCont{i}`를 먼저 읽고 없으면 `prmsCont{i}`로 대체**하도록 짠다.
- `prmsRealmName{i}`(공약분야)는 대부분 비어 있다. 2022년 1,248건 중 0건, 2026년 3,330건 중 5건에만 값이 있었다(polis-korea). 2026년 교육감 응답에는 이 필드 자체가 없었다는 보고도 있다(15678910).
- 2026년 9회 지방선거에서는 모든 후보가 5개 공약을 냈다(666명 전원 5개). 슬롯 6~10은 비어 있거나 필드가 아예 없으므로, 모든 필드를 **옵션으로 취급**한다.
- 문서상 필드 크기는 255이지만 실제 본문은 훨씬 길다(수백~수천 자). DB 컬럼은 `text`로 잡는다.
- 교육감은 `wiwName`이 공란이다(문서). `partyName`이 공란인지는 미확인.

### 제공 범위와 시점
- 문서: 선거가 끝나기 전에는 후보자 공약을 제공하고, "선거종료 및 데이터 갱신 이후에는 당선인 정보만" 제공한다.
- 실측(polis-korea, 2026-08-04 기준): 9회 지방선거(2026-06)의 낙선자 공약이 아직 남아 있었다. 21대 대선(2025-06)과 7·8회 지방선거의 낙선자 공약은 없었다. 즉 **낙선자 공약은 선거 후 2~14개월 사이에 사라진다.** 오늘(2026-09-22) 시점에 9회 낙선자 공약이 남아 있는지는 **미확인**이다.
- 실측 하한: 2017년 19대 대선부터 조회된다. 2014년 6회 지방선거는 INFO-03이다(polis-korea).

---

## 2. 당선인정보 — `WinnerInfoInqireService2` (data.go.kr 15000864)

- 엔드포인트: `http://apis.data.go.kr/9760000/WinnerInfoInqireService2/getWinnerInfoInqire`. 확인. 오퍼레이션은 하나다.
- 가이드 v3.11(2025-02-12), 페이지 수정일 2026-01-16.

### 요청
| 파라미터 | 필수 | 비고 |
|---|---|---|
| `serviceKey` | ✅ | |
| `pageNo`, `numOfRows` | (가이드 표기는 필수) | numOfRows 최대 100 → 페이지를 넘기며 받는다 |
| `resultType` | – | xml/json |
| `sgId` | ✅ | |
| `sgTypecode` | ✅ | |
| `sdName` | – (옵션) | 시도명. 예: `전국`, `서울특별시` |
| `sggName` | – (옵션) | 선거구명. 예: `대한민국`, `종로구` |

`sgId`와 `sgTypecode`만으로도 전국 목록을 페이지 단위로 받을 수 있다(k-vote-cli, polis-korea, kimbomi-site). 확인.

### 응답 item 필드 (철자는 그대로 옮김)
`num`, `sgId`, `sgTypecode`, `huboid`, `sggName`, `sdName`, `wiwName`, `giho`, `gihoSangse`, `jdName`, `name`, `hanjaName`, `gender`, `birthday`, `age`, `addr`, `jobId`, `job`, `eduId`, `edu`, `career1`, `career2`, `dugsu`, `dugyul`
- 요청하신 목록과 비교하면 `giho`와 `gihoSangse`가 **추가로** 있다. 요청하신 필드는 철자까지 모두 일치한다.
- `age`는 선거일 기준 나이다. `addr`는 상세주소를 뺀 주소이며, info.nec.go.kr에서 역대 선거로 이관된 선거는 주소를 주지 않는다(빈 값). `dugyul`은 %이고 예시 값은 `49.42`다. `giho`는 비례대표일 때 추천순위다.
- 실제 XML 예시(21대 대선): k-vote-cli `internal/nec/testdata/api_winners.xml`.

### `cnddtId == huboid`
**확인.** 가이드 원문(위)에 근거가 있고, 실사용에서도 맞아떨어진다.
- 8회 지방선거 당선인 API에서 받은 `huboid`로 공약 API를 조회하면 250명 중 230명의 공약이 나온다(polis-korea).
- 2022년 서울시장 당선인의 huboid를 cnddtId로 넣으면 INFO-00과 prmsCnt=5가 나온다(SmileJune).
- 같은 인물의 huboid는 후보자 API와 당선인 API에서 같다(SmileJune, 2026년 사례).

### 9회(2026) 당선인 제공 여부 — **미확인(간접 증거로는 제공 중일 가능성이 높음)**
- 2026-06-11 기준으로는 OpenAPI에 올라와 있지 않았다(INFO-03, polis-korea 문서).
- data.go.kr 페이지의 "제공 범위(2026년 기준)"에는 전국동시지방선거가 "제3회 ~ 제8회"로 적혀 있다. 다만 이 페이지는 선거 전인 2026-01-16에 수정된 뒤 갱신되지 않았다. 공식 방침은 "통상 2개월 이내에 데이터 이관 및 검증 후 제공"이다.
- kimbomi0603/kimbomi-site의 `data/pledge.json`(built_at 2026-09-17)에는 sgId 20260603으로 광역·기초 단체장 246곳의 당선인이 들어 있고, `dugsu`와 `dugyul`까지 채워져 있다. 출처는 "당선인정보·후보자공약"으로 표기되어 있다. → 9월 중순에는 당선인 API가 제공 중이었을 가능성이 높다. **실제 키로 호출해 확인할 것**: `sgId=20260603&sgTypecode=3`.

---

## 3. 코드정보 — `CommonCodeService` (data.go.kr 15000897)

- 기본 URL: `http://apis.data.go.kr/9760000/CommonCodeService`. 가이드 v3.12.
- 오퍼레이션 6개: `getCommonSgCodeList`(선거코드), `getCommonGusigunCodeList`(구시군코드), `getCommonSggCodeList`(선거구코드), `getCommonPartyCodeList`(정당코드), `getCommonJobCodeList`(직업코드), `getCommonEduBckgrdCodeList`(학력코드). 확인.

### `getCommonSgCodeList` — 선거코드
- 요청: `serviceKey`, `pageNo`, `numOfRows`, `resultType`. **sgId 파라미터는 없고 전체 목록을 준다.**
- 응답: `num`, `sgId`, `sgTypecode`, `sgName`, `sgVotedate`
- sgTypecode 전체 목록(가이드): 0 대표선거명, 1 대통령, 2 국회의원, 3 시도지사, 4 구시군장, 5 시도의원, 6 구시군의회의원, 7 국회의원비례대표, 8 광역의원비례대표, 9 기초의원비례대표, 10 교육의원, 11 교육감

### `getCommonSggCodeList` — 선거구코드
- 요청: `serviceKey`, `pageNo`, `numOfRows`, `resultType`, **`sgId`(필수)**, **`sgTypecode`(필수)**. 확인(가이드와 페이지). 제3자 문서에는 `sdName`과 `wiwName`도 받는다고 되어 있으나 공식 명세에는 없다(미확인).
- 응답: `num`, `sgId`, `sgTypecode`, `sggName`, `sdName`, `wiwName`, `sggJungsu`(선출정수), `sOrder`

### `getCommonGusigunCodeList` — 구시군코드 (참고)
- 요청: `sgId`(필수), `sdName`(옵션). 응답: `num`, `sgId`, `sdName`, `wiwName`, `wOrder`

---

## 4. sgId

| 선거 | sgId | 상태 |
|---|---|---|
| 제8회 전국동시지방선거 (2022-06-01) | **`20220601`** | 확인. 이 sgId로 후보자·공약 API가 INFO-00을 반환한다(SmileJune). polis-korea 8th-local의 `sg_id`도 이 값이다. |
| 제9회 전국동시지방선거 (2026-06-03) | **`20260603`** | 확인. `getCommonSgCodeList`가 이 값을 반환한다(SmileJune 2026-05-18). 2026년 선거의 sgTypecode는 3, 4, 5, 6, 8, 9, 11이다. |

9회 데이터 상태 (2026-09-22 기준)
- 공약 API: 9회 공약이 **조회된다**. 확인: 2026-05-25(SmileJune), 2026-06-03(15678910 교육감 58명·시도지사·구시군장), 2026-08-06(polis-korea, 전체 후보 697명 명부 중 666명의 공약 3,330건).
- 당선인 API: 위 §2를 보라(미확인, 가능성 높음).
- ⚠ 2026년에는 광주·전남 지역 일부 레코드의 `sdName`이나 `sggName`이 `전남광주통합특별시`로 나온다(SmileJune, biguse74). sdName으로 필터하거나 조인할 때 주의한다.

---

## 5. 수집기 구현 체크리스트 (위 근거에서 도출)
1. `params={"serviceKey": unquote(KEY), "resultType": "json", "numOfRows": 100, "pageNo": n, ...}` 형태로 보내고, `totalCount`를 보고 다음 페이지를 받는다.
2. 파싱 순서:
   - 먼저 `OpenAPI_ServiceResponse`(게이트웨이 오류)인지 검사한다.
   - 다음으로 `response.header.resultCode`를 본다. `INFO-00`과 `00`은 성공, `INFO-03`과 `ERROR-03`은 빈 결과, 그 밖은 예외로 처리한다.
   - 마지막으로 `response.body.items.item`을 list로 정규화한다. dict나 빈 값도 들어올 수 있다. 구형 루트(오퍼레이션명)도 대비해 둔다.
3. 공약 본문은 `item.get(f"prmmCont{i}") or item.get(f"prmsCont{i}")`로 읽는다. `prmsCnt`는 참고용으로만 쓰고, 실제 개수는 `prmsTitle{i}`가 채워진 슬롯으로 판정한다.
4. 조인: 당선인 API의 `huboid`를 공약 API의 `cnddtId`로 넣는다. sgTypecode는 3, 4, 11만 쓴다(지방선거 기준).
5. 502/504는 지수 백오프로 재시도한다. 호출 간 간격은 0.1~0.15초 정도로 둔다(30tps와 일일 한도를 고려).

---

## 출처
- data.go.kr 선거공약 정보: https://www.data.go.kr/data/15040587/openapi.do (첨부 `OpenAPI활용가이드(선거공약정보)_v2.15.zip`)
- data.go.kr 당선인 정보: https://www.data.go.kr/data/15000864/openapi.do (첨부 `OpenAPI활용가이드(당선인정보)_v3.11.zip`)
- data.go.kr 코드 정보: https://www.data.go.kr/data/15000897/openapi.do (첨부 `OpenAPI활용가이드(코드정보)_v3.12.zip`, 오퍼레이션 상세는 `/tcs/dss/selectApiDetailFunction.do`에서 조회)
- data.go.kr 후보자 정보: https://www.data.go.kr/data/15000908/openapi.do (가이드 v4.3)
- NEC 개방포털 선거공약: http://data.nec.go.kr/open-data/api.do?dataId=14
- polis-korea 공약 수집기와 실측 주석: https://github.com/YangSeungWon/polis-korea/blob/HEAD/scripts/fetch/fetch_pledges.py , 데이터 https://github.com/YangSeungWon/polis-korea/tree/HEAD/data/pledges , 9회 당선인 INFO-03 기록 https://github.com/YangSeungWon/polis-korea/blob/HEAD/docs/local-seats-provenance.md
- SmileJune 실호출 검증 기록: https://github.com/SmileJune/before-you-vote/blob/HEAD/docs/openapi-validation.md , https://github.com/SmileJune/before-you-vote/blob/HEAD/docs/nec-api-field-inventory.md
- 15678910/budget 교육감 공약 수집(2026): https://github.com/15678910/budget/blob/HEAD/scripts/fetch-pledges.mjs
- minskapo/nec-2026-pledges: https://github.com/minskapo/nec-2026-pledges/blob/HEAD/collect/02_fetch_pledges.py
- k-vote-cli XML 봉투와 fixture: https://github.com/JungHoonGhae/k-vote-cli/blob/HEAD/internal/nec/api.go , https://github.com/JungHoonGhae/k-vote-cli/blob/HEAD/internal/nec/testdata/api_winners.xml
- JSON 봉투 신형: https://github.com/bit2r/gpt-ds/blob/HEAD/docs/ingest_web.html (2024). 구형: https://github.com/bit2r/map_challenge/blob/HEAD/docs/legislators.html (2023)
- kimbomi-site 당선인과 공약 JSON 프록시, 2026 데이터: https://github.com/kimbomi0603/kimbomi-site/blob/HEAD/api/contract.js , https://github.com/kimbomi0603/kimbomi-site/blob/HEAD/data/pledge.json
- cow-coding/V.O.T.E (`prmmCont1` 출력, 2021): https://github.com/cow-coding/V.O.T.E/blob/HEAD/data_files/election_database.ipynb
- Encoding/Decoding 키 안내: https://wikidocs.net/268599 , https://datadoctorblog.com/2025/03/18/Py-Crawling-API-gov-Keys/

---

## 6. 실제 수집 결과 (2026-09-22, 국내 PC에서 실행)

`python -m pledge_pipeline.nec.collect --sg-id <sgId>` — 오류 0건.

| 항목 | 민선8기 (20220601) | 민선9기 (20260603) |
| :- | -: | -: |
| 당선인: 시도지사 / 구시군장 / 교육감 | 17 / 226 / 17 = **260** | 16 / 227 / 16 = **259** |
| 공약 응답이 있는 당선인 | 250 | 256 |
| 공약 수 | **1,248** (당선인당 5개, 1명만 3개) | **1,280** (전원 5개) |
| 공약 본문(`prmmCont`) 비어 있음 | 0 | 0 |
| 공약 분야(`prmsRealmName`) 채워짐 | 0 | 5 |
| 본문 길이 중앙값 / 최대 | 505 / 4,205자 | 616 / 10,750자 |
| 정당 공란 | 17 (= 교육감) | 16 (= 교육감) |

- 8기 공약 1,248건은 제3자 수집 결과(polis-korea)와 같은 수치다.
- **공약이 없는 당선인**의 사유는 수집기가 `summary.json`에 추정해 적는다.
  - 8기 10명: 무투표 당선(득표수 0) 6명, 경선 당선인데 공약 없음 4명. 선거공약서는 임의 제출이라 미제출로 추정한다.
  - 9기 3명: 모두 무투표 당선.
  - 방법론 페이지에 "공약 데이터 없음" 사유로 표시할 것.
- **시도명 표기**
  - 8기는 당시 명칭(`강원도`, `전라북도`)을 쓴다.
  - 9기는 광역·교육감에 `전남광주통합특별시`, 기초에 `광주광역시`/`전라남도`가 섞여 시도명이 18종이다. 지역별로 묶거나 기수를 넘어 비교하려면 시도 정규화 규칙이 필요하다.
- 키 활용신청은 **API별로 따로** 한다. 선거공약만 승인된 상태에서 당선인정보를 호출하면 게이트웨이 코드 `30`(SERVICE_KEY_IS_NOT_REGISTERED_ERROR)이 온다. 승인 직후에는 몇 분 안에 반영됐다.
