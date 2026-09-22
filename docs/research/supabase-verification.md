# Supabase 배포 검증 (2026-09-22)

프로젝트 `pledge-tracker` (ref `lbdjcmmqdbezndokblky`, ap-northeast-2)에 초기 마이그레이션을 적용한 뒤 독립 검증을 돌렸다.
보안·접근, 스키마 일치, 성능·파이프라인 호환 세 방향으로 나눠 검증했고, 비평 단계에서 빠진 점검을 보완했다. 이어 중간 이상 이슈마다 따로 재현을 시도했다.
**점검 118개 중 실패 7개였고 치명적인 문제는 없었다.**

## 통과한 핵심 점검

- **적용본 일치**: 원격 `schema_migrations`에 기록된 구문의 md5가 `supabase/migrations/20260922120158_init.sql`과 같다(바이트 단위 동일).
- **공개 키 접근 매트릭스** (publishable 키와 legacy anon JWT 모두 확인)
  - 공개 테이블 11개와 `current_judgments`는 읽기 200이다.
  - 내부 테이블 4개(`qa_cache`, `rate_limits`, `golden_set`, `qa_golden_set`)는 401 `permission denied`다.
  - POST/PATCH/DELETE와 upsert는 모두 401이다. 뷰에 DELETE를 보내면 500(`cannot delete from view`)이 나오지만 이것도 거부로 본다.
  - 탐침 후 데이터 변경은 없었다.
- **노출 범위**
  - 키 없이 요청하면 401이다.
  - `extensions`/`storage`/`auth` 스키마는 노출되지 않는다(`public`, `graphql_public`만 노출).
  - OpenAPI 스펙 조회에는 secret 키가 필요하다.
  - pg_graphql은 설치되어 있지 않다.
- **권한 구조**
  - public 테이블 15개 모두 RLS가 켜져 있다.
  - 정책은 공개 11개 테이블의 SELECT 정책뿐이다.
  - anon/authenticated는 공개 12개 relation에 SELECT만 갖는다. 시퀀스 권한은 없다.
  - postgres 역할의 기본 권한으로는 이후 생성되는 테이블·시퀀스가 비공개다.
- **확장**: `vector`는 `extensions` 스키마에 있다.
- **보안 advisor**: `rls_enabled_no_policy`(INFO)만 나온다. 대상은 내부 테이블 4개이고 의도한 결과다.

## 발견 사항과 조치

| 발견 | 조치 |
| :- | :- |
| 유휴 방지 핑이 주 2회뿐이다. 공식 문서 기준은 "매일 몇 번의 요청" | 매일 실행으로 바꾸고, 행이 있는 테이블 3개를 조회한다 |
| 이후 `public`에 만드는 함수는 anon이 실행할 수 있다(Supabase 기본 권한 + Postgres 전역 PUBLIC 기본값) | 마이그레이션 002에서 anon/authenticated 기본 EXECUTE를 회수한다. PUBLIC 기본값은 스키마 단위로 회수할 수 없으므로 CI가 anon 실행 가능 함수를 검사한다 |
| CI 스텁에 Supabase 기본 권한이 없어서, 권한 최소화 구문이 빠져도 CI가 통과한다 | 스텁에 Supabase의 기본 권한(ALL 부여)을 재현한다 |
| `pledge_id`는 원문 순번으로, `ord`는 정규화한 값으로 만들어 서로 어긋날 수 있다 | 둘 다 같은 정규화 값을 쓴다. `(winner_id, ord)`가 중복되면 적재를 중단한다 |
| 재적재할 때 `fetched_at`이 갱신되지 않는다 | 수집 시점(`summary.json`)을 행에 넣어 upsert로 갱신한다 |
| 원천에서 사라진 공약을 알 수 없다 | 적재 후 목록을 경고로 출력한다. 삭제는 하지 않는다: `pledges`를 지우면 `judgments`가 cascade로 사라져 판정 이력 공개 원칙이 깨진다 |
| `DATABASE_URL`에 `sslmode`가 없어 libpq 기본값 `prefer`가 쓰인다 | `sslmode`가 없으면 `require`를 기본으로 쓴다. `.env.example`에도 반영했다 |
| 트랜잭션 풀러(6543)는 prepared statement를 지원하지 않는다 | `prepare_threshold=None`으로 설정했다 |
| gitleaks 기본 규칙이 Postgres URI 비밀번호와 `sb_secret_` 키를 잡지 못한다 | `.gitleaks.toml`에 규칙 2개를 추가했다(가짜 값으로 탐지 확인, 자리표시자는 제외) |
| 중복 인덱스 2개(unique 제약 인덱스와 겹침) | 마이그레이션 002에서 제거한다. `judgments` 인덱스는 `current_judgments` 정렬에 맞췄다 |

## 대시보드 설정 (운영자 조치, 2026-09-22 반영 확인)

보안 설정이라 코드로 바꾸지 않고 대시보드에서 직접 설정했다. 반영 여부는 외부 호출로 확인했다.

| 설정 | 상태 | 확인 방법 |
| :- | :- | :- |
| Database → SSL Configuration → Enforce SSL | ✅ | 평문(`sslmode=disable`) 접속이 인증 전에 `FATAL: (ESSLREQUIRED)`로 거부됨 |
| Database 비밀번호를 대시보드 생성값으로 재설정 | ✅ | 새 `DATABASE_URL`로 TLS 접속 성공(`pg_stat_ssl.ssl = true`) |
| Authentication → 신규 가입 차단 | ✅ | `/auth/v1/settings`에서 `disable_signup = true`, 가입 요청 시 422 `signup_disabled` |
| Settings → API Keys → Legacy(JWT) 키 비활성화 | ✅ | legacy anon JWT로 요청하면 401 "Legacy API keys are disabled". 같은 방식의 service_role JWT도 함께 무효 |
| Data API → Exposed schemas에서 `graphql_public` 제거 (선택) | 미적용 | 노출 스키마가 여전히 `public, graphql_public`. pg_graphql이 설치되어 있지 않아 실제로 노출되는 것은 없다 |

조치 후 회귀 점검 결과:
- 공개 키로 공개 테이블을 읽으면 200이다.
- 내부 테이블 조회와 쓰기·삭제는 401이다.
- anon/authenticated 테이블 권한은 SELECT 12건 그대로다.
- postgres 역할의 public 기본 권한에는 anon/authenticated가 없다.
- `supabase_admin`의 기본 권한은 플랫폼 기본값이라 남아 있다. supabase_admin이 만드는 객체(예: 대시보드에서 public에 설치하는 확장)에만 적용된다. 따라서 확장은 항상 `extensions` 스키마에 설치한다.

주의: 대시보드 Data API 설정의 **Exposed tables**가 "0 of 16"으로 보이는 것은 anon에게 SELECT만 부여했기 때문이다. 조회는 정상이다. 여기서 테이블을 켜면 권한 최소화가 되돌려질 수 있으므로 쓰지 않는다. 공개 범위는 마이그레이션으로만 바꾼다.

## 참고

- `current_judgments`는 생성 시점의 `judgments` 컬럼 목록으로 고정된다. `judgments`에 컬럼을 추가하는 마이그레이션에서는 뷰도 다시 만든다.
- Storage 버킷은 없다. 버킷을 도입할 때는 비공개로 만들고, bucket_id로 한정한 SELECT 정책만 추가한다.
