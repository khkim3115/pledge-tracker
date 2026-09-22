-- 배포 검증 결과 반영 (docs/research/supabase-verification.md)

-- 1) public 스키마에 이후 생성되는 함수: anon/authenticated 기본 EXECUTE 회수.
--    PUBLIC의 EXECUTE는 Postgres 전역 기본값이라 스키마 단위로 회수할 수 없다.
--    → 함수를 만들 때 `revoke execute on function ... from public, anon, authenticated`를 함께 쓰고,
--      공개 RPC만 명시적으로 grant한다. CI(migrations job)가 anon 실행 가능 함수를 검사한다.
alter default privileges in schema public revoke execute on functions from anon, authenticated;

-- 2) unique 제약 인덱스와 겹치는 인덱스 제거
drop index if exists public.pledges_winner_idx;       -- unique (winner_id, ord)가 커버
drop index if exists public.task_snapshots_task_idx;  -- unique (task_id, as_of, content_hash)가 커버

-- 3) current_judgments의 distinct on 정렬(pledge_id, judged_at desc, judgment_id desc)과 일치
drop index if exists public.judgments_pledge_idx;
create index judgments_pledge_idx on public.judgments (pledge_id, judged_at desc, judgment_id desc);
