-- pledge-tracker 초기 스키마 (docs/PROJECT.md 7장)
-- 원칙: 원본값(raw)과 정규화값 분리 저장 / 스냅샷은 덮어쓰지 않고 누적 / 판정은 모델·시점 기록(재현성)
-- 쓰기는 파이프라인(service role, RLS 우회)만 한다. 공개 테이블은 anon/authenticated 읽기 전용.

create extension if not exists vector with schema extensions;

-- ---------------------------------------------------------------------------
-- 코드 테이블
-- ---------------------------------------------------------------------------

-- 매니페스토 표준 5분류
create table normalized_statuses (
  code       text primary key,
  label_ko   text not null unique,
  sort_order smallint not null
);

insert into normalized_statuses (code, label_ko, sort_order) values
  ('completed',  '완료',           1),
  ('continuing', '이행후계속추진', 2),
  ('on_track',   '정상추진',       3),
  ('partial',    '일부추진',       4),
  ('stalled',    '보류·폐기',      5);

-- ---------------------------------------------------------------------------
-- 기준 데이터 (선관위 API)
-- ---------------------------------------------------------------------------

create table winners (
  winner_id   text primary key,              -- '{sg_id}-{huboid}'
  sg_id       text not null,                 -- 선거ID: 20220601(민선8기), 20260603(민선9기)
  sg_type     smallint not null,             -- sgTypecode: 3 시도지사, 4 구시군장, 11 교육감
  huboid      text not null,                 -- 선관위 후보자ID (= 공약 API cnddtId)
  term        smallint not null,             -- 민선 기수: 8, 9
  sido_name   text not null,
  sgg_name    text not null,                 -- 선거구명 (예: 경기도, 수원시)
  wiw_name    text,                          -- 구시군명
  region      text not null,                 -- 표시용 지역명 (예: '경기도', '경기도 수원시')
  party       text,
  name        text not null,
  raw         jsonb not null,                -- 원본 응답 보존
  fetched_at  timestamptz not null default now(),
  unique (sg_id, huboid)
);

create index winners_region_idx on winners (term, sg_type, sido_name);

create table pledges (
  pledge_id   text primary key,              -- '{winner_id}-{ord}'
  winner_id   text not null references winners on delete cascade,
  ord         smallint not null,             -- 공약 순번 (prmsOrd)
  field       text,                          -- 공약 분야 (prmsRealmName)
  title       text not null,
  content     text,
  source      text not null default 'nec_api',
  term        smallint not null,
  raw         jsonb,
  fetched_at  timestamptz not null default now(),
  unique (winner_id, ord)
);

create index pledges_winner_idx on pledges (winner_id);

-- ---------------------------------------------------------------------------
-- 운영: 어댑터 (지자체 크롤러)
-- ---------------------------------------------------------------------------

create table adapters (
  adapter_id      text primary key,          -- 예: 'gyeonggi', 'seoul'
  region          text not null,
  term            smallint not null,
  base_url        text not null,
  parser_type     text not null,             -- html | pdf | hwp | xlsx | api
  enabled         boolean not null default true,
  last_success_at timestamptz,
  last_error      text,
  created_at      timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- 이행 데이터 (지자체 자가보고)
-- ---------------------------------------------------------------------------

create table status_mapping (
  adapter_id        text not null references adapters on delete cascade,
  raw_status        text not null,           -- 원문 그대로 (보류/폐기도 구분해 보존)
  normalized_status text not null references normalized_statuses,
  primary key (adapter_id, raw_status)
);

create table tasks (
  task_id     text primary key,              -- '{adapter_id}:{external_id}'
  adapter_id  text not null references adapters,
  external_id text not null,                 -- 지자체 과제번호/식별자
  term        smallint not null,
  name        text not null,
  field       text,
  dept        text,
  budget_raw  text,                          -- 원문 표기 그대로
  budget_krw  bigint,                        -- 파싱 가능한 경우만
  raw_status  text,                          -- 최신 스냅샷 기준
  source_url  text,
  fetched_at  timestamptz not null default now(),
  unique (adapter_id, external_id)
);

create table task_snapshots (
  snapshot_id       bigint generated always as identity primary key,
  task_id           text not null references tasks on delete cascade,
  as_of             date not null,           -- 기준일 (예: 2026-06-30). 공개 주기가 반기·분기·비정기로 섞여 날짜로 저장
  period_label      text,                    -- 원문 표기 (예: '2026년 6월 말 기준')
  raw_status        text,
  normalized_status text references normalized_statuses,
  progress_rate     numeric(5, 2),           -- 진척률(%) 제공 시
  progress_text     text,                    -- 추진실적 원문
  content_hash      text not null,           -- diff 감지: 변경분만 재처리
  source_url        text,
  fetched_at        timestamptz not null default now(),
  unique (task_id, as_of, content_hash)
);

create index task_snapshots_task_idx on task_snapshots (task_id, as_of desc);

-- ---------------------------------------------------------------------------
-- AI 산출물
-- ---------------------------------------------------------------------------

-- 공약↔과제 매칭. task_id NULL = 'NONE' (실천계획 누락 공약)
create table matches (
  match_id   bigint generated always as identity primary key,
  pledge_id  text not null references pledges on delete cascade,
  task_id    text references tasks on delete cascade,
  similarity real,                           -- 1단계 임베딩 코사인 유사도
  method     text not null,                  -- 'embedding' | 'llm' | 'human'
  model      text,
  confirmed  boolean not null default false,
  created_at timestamptz not null default now(),
  unique nulls not distinct (pledge_id, task_id, method)
);

create index matches_task_idx on matches (task_id);

-- 판정은 누적(append-only). 현재 판정은 current_judgments 뷰로 조회하고, 변경 이력은 그대로 공개한다.
create table judgments (
  judgment_id          bigint generated always as identity primary key,
  pledge_id            text not null references pledges on delete cascade,
  verdict              text not null,        -- JudgmentSchema 확정(4주차) 후 check 제약 추가
  confidence           real check (confidence between 0 and 1),
  rationale            text,
  evidence             jsonb not null default '[]',  -- [{chunk_id, quote, source_url}]
  self_reported_status text references normalized_statuses,
  discrepancy          boolean not null default false,
  tier                 text not null default 'primary',  -- 'primary' | 'escalated' (캐스케이드)
  model                text not null,
  prompt_version       text not null,
  input_hash           text,                 -- 블라인딩된 입력의 해시(재현성)
  judged_at            timestamptz not null default now()
);

create index judgments_pledge_idx on judgments (pledge_id, judged_at desc);

create view current_judgments with (security_invoker = true) as
select distinct on (pledge_id) *
from judgments
order by pledge_id, judged_at desc, judgment_id desc;

-- 임베딩 차원은 모델 확정 전 임시값(768). 변경 시 데이터 적재 전에 마이그레이션으로 교체.
create table evidence_chunks (
  chunk_id   bigint generated always as identity primary key,
  task_id    text not null references tasks on delete cascade,
  text       text not null,
  embedding  extensions.vector(768),
  source_url text,
  page       int,
  fetched_at timestamptz not null default now()
);

create index evidence_chunks_task_idx on evidence_chunks (task_id);
create index evidence_chunks_embedding_idx on evidence_chunks
  using hnsw (embedding extensions.vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- 교차검증 (LLM 추출 후 사람 검수 완료분만 적재)
-- ---------------------------------------------------------------------------

create table manifesto_grades (
  region      text not null,
  year        smallint not null,
  grade       text,
  scores      jsonb,
  source_doc  text not null,
  verified_at timestamptz not null,
  primary key (region, year)
);

-- ---------------------------------------------------------------------------
-- Q&A (비공개: 서버 전용)
-- ---------------------------------------------------------------------------

create table qa_cache (
  query_hash       text primary key,
  normalized_query text not null,
  response         jsonb not null,
  created_at       timestamptz not null default now(),
  hit_count        int not null default 0
);

-- Upstash Redis 사용 시 미사용
create table rate_limits (
  key          text not null,
  window_start timestamptz not null,
  count        int not null default 0,
  primary key (key, window_start)
);

-- ---------------------------------------------------------------------------
-- 골든셋 (비공개: 평가용)
-- ---------------------------------------------------------------------------

create table golden_set (
  pledge_id            text primary key references pledges on delete cascade,
  human_match_task_ids text[] not null default '{}',  -- 빈 배열 = NONE
  human_verdict        text,
  note                 text,
  labeled_at           timestamptz not null default now()
);

create table qa_golden_set (
  id                bigint generated always as identity primary key,
  query             text not null,
  query_type        text not null check (query_type in ('sql', 'semantic', 'out_of_scope', 'political')),
  expected_behavior text not null,
  labeled_at        timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- RLS: 전 테이블 활성화. 공개 테이블만 읽기 정책 부여 (쓰기 정책 없음 = service role 전용)
-- ---------------------------------------------------------------------------

do $$
declare
  t text;
begin
  foreach t in array array[
    'normalized_statuses', 'winners', 'pledges', 'adapters', 'status_mapping',
    'tasks', 'task_snapshots', 'matches', 'judgments', 'evidence_chunks', 'manifesto_grades',
    'qa_cache', 'rate_limits', 'golden_set', 'qa_golden_set'
  ] loop
    execute format('alter table public.%I enable row level security', t);
  end loop;

  foreach t in array array[
    'normalized_statuses', 'winners', 'pledges', 'adapters', 'status_mapping',
    'tasks', 'task_snapshots', 'matches', 'judgments', 'evidence_chunks', 'manifesto_grades'
  ] loop
    execute format(
      'create policy "public read" on public.%I for select to anon, authenticated using (true)', t
    );
  end loop;
end
$$;
