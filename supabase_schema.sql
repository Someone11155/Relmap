-- ============================================================================
-- 인물 관계도 — Supabase 스키마 (Supabase 대시보드 → SQL Editor 에 통째로 붙여 넣고 Run)
--
-- 보안 모델: 방 주소(room id)를 아는 사람만 그 방에 들어올 수 있습니다.
--   · 접속자는 익명 로그인(Authentication → Sign In / Providers → Anonymous Sign-Ins 켜기)으로 사용자 ID를 받고,
--   · join_room() 으로 방에 '입장 등록'을 해야 그 방의 데이터를 읽고 쓸 수 있습니다.
--   · 표는 직접 읽기/쓰기가 막혀 있고(RLS), 쓰기는 아래 함수로만 가능합니다.
-- 방 주소가 곧 열쇠이므로, 주소는 믿을 만한 사람에게만 공유하세요.
-- ============================================================================

create sequence if not exists public.items_ver;

create table if not exists public.rooms (
  id         text primary key check (id ~ '^[A-Za-z0-9_-]{8,64}$'),
  seeded     boolean not null default false,        -- 첫 입장자가 문서를 채웠는지
  created_at timestamptz not null default now()
);

-- 저장 관련 열: 로그인한 사람이 '저장'하면 owner/title/saved_at 이 채워짐 (이미 만든 DB 에서 다시 실행해도 안전)
alter table public.rooms add column if not exists owner    uuid;
alter table public.rooms add column if not exists title    text;
alter table public.rooms add column if not exists saved_at timestamptz;

create table if not exists public.room_members (
  room      text not null references public.rooms(id) on delete cascade,
  uid       uuid not null,
  joined_at timestamptz not null default now(),
  primary key (room, uid)
);

-- 인물('n')과 관계선('l')을 한 표에 저장. 삭제는 행을 지우지 않고 deleted=true 로 표시
-- (Realtime 의 DELETE 이벤트는 방별로 거를 수 없고 RLS 도 적용되지 않기 때문)
create table if not exists public.items (
  room       text not null references public.rooms(id) on delete cascade,
  kind       text not null check (kind in ('n','l')),
  id         text not null check (length(id) between 1 and 64),
  data       jsonb not null default '{}'::jsonb,
  deleted    boolean not null default false,
  ver        bigint not null default nextval('public.items_ver'),   -- 행이 바뀔 때마다 커지는 번호
  updated_at timestamptz not null default now(),
  primary key (room, kind, id)
);

-- ---- RLS: 표는 직접 접근 금지, items 는 '내가 입장한 방'만 읽기 가능 ---------------
alter table public.rooms        enable row level security;
alter table public.room_members enable row level security;
alter table public.items        enable row level security;

revoke all on public.rooms, public.room_members, public.items from anon, authenticated;
grant select on public.items to authenticated;

create or replace function public.is_member(p_room text)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.room_members m where m.room = p_room and m.uid = (select auth.uid()))
$$;

drop policy if exists items_select_member on public.items;
create policy items_select_member on public.items for select to authenticated
  using (public.is_member(room));

-- ---- 함수 -----------------------------------------------------------------------
-- 방 입장 등록. 방이 없으면 만들고, 이미 문서가 채워졌는지(true/false)를 돌려줌
create or replace function public.join_room(p_room text)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_seeded boolean;
begin
  if v_uid is null then raise exception 'not authenticated' using errcode = '28000'; end if;
  if p_room !~ '^[A-Za-z0-9_-]{8,64}$' then raise exception 'invalid room id' using errcode = '22023'; end if;
  insert into public.rooms (id) values (p_room) on conflict (id) do nothing;
  insert into public.room_members (room, uid) values (p_room, v_uid) on conflict do nothing;
  select seeded into v_seeded from public.rooms where id = p_room;
  return v_seeded;
end $$;

-- 변경 적용. p_ops 는 아래 모양의 배열 (순서대로 적용되고, 전체가 한 트랜잭션)
--   {"k":"n","id":"...","put":{...전체...}}            새로 만들기 / 통째로 덮어쓰기(삭제된 것 되살리기 포함)
--   {"k":"n","id":"...","set":{...},"rm":["필드"]}     일부 필드만 바꾸기 (다른 사람이 바꾼 다른 필드는 유지)
--   {"k":"n","id":"...","del":true}                     삭제
-- 반환: 바뀐 항목들의 최종 상태 [{k,id,ver,data,deleted}]
create or replace function public.apply_ops(p_room text, p_ops jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare op jsonb; v_k text; v_id text; res jsonb;
begin
  if not public.is_member(p_room) then raise exception 'not a member' using errcode = '42501'; end if;
  if p_ops is null or jsonb_typeof(p_ops) <> 'array' or jsonb_array_length(p_ops) > 500 then
    raise exception 'bad ops' using errcode = '22023';
  end if;
  for op in select value from jsonb_array_elements(p_ops) loop
    v_k := op->>'k'; v_id := op->>'id';
    if v_k is null or v_k not in ('n','l') or v_id is null or length(v_id) not between 1 and 64 then
      raise exception 'bad op' using errcode = '22023';
    end if;
    if op ? 'put' then
      if jsonb_typeof(op->'put') <> 'object' or length((op->'put')::text) > 1500000 then
        raise exception 'bad data' using errcode = '22023';
      end if;
      insert into public.items (room, kind, id, data, deleted, ver, updated_at)
      values (p_room, v_k, v_id, op->'put', false, nextval('public.items_ver'), now())
      on conflict (room, kind, id) do update
        set data = excluded.data, deleted = false, ver = excluded.ver, updated_at = excluded.updated_at;
    elsif op ? 'del' then
      update public.items set data = '{}'::jsonb, deleted = true, ver = nextval('public.items_ver'), updated_at = now()
       where room = p_room and kind = v_k and id = v_id and not deleted;
    elsif op ? 'set' then
      if jsonb_typeof(op->'set') <> 'object' or length((op->'set')::text) > 1500000 then
        raise exception 'bad data' using errcode = '22023';
      end if;
      update public.items
         set data = (data - coalesce(array(select jsonb_array_elements_text(coalesce(op->'rm', '[]'::jsonb))), '{}'::text[]))
                    || (op->'set'),
             ver = nextval('public.items_ver'), updated_at = now()
       where room = p_room and kind = v_k and id = v_id and not deleted;
    end if;
  end loop;
  select coalesce(jsonb_agg(jsonb_build_object('k', i.kind, 'id', i.id, 'ver', i.ver, 'data', i.data, 'deleted', i.deleted)), '[]'::jsonb)
    into res
    from public.items i
   where i.room = p_room
     and (i.kind, i.id) in (select o->>'k', o->>'id' from jsonb_array_elements(p_ops) o);
  return res;
end $$;

-- 방의 첫 입장자가 '내가 문서를 채울게요' 하고 방을 선점. 이미 누가 선점했으면 false
-- (선점한 사람이 apply_ops 로 자기 문서를 올림. 먼저 온 사람 것이 방의 내용이 됨)
create or replace function public.seed_room(p_room text)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_n int;
begin
  if not public.is_member(p_room) then raise exception 'not a member' using errcode = '42501'; end if;
  update public.rooms set seeded = true where id = p_room and not seeded;
  get diagnostics v_n = row_count;
  return v_n > 0;
end $$;

-- ---- 저장(로그인한 사람만) -------------------------------------------------------
-- 게스트 = 익명 로그인 사용자(JWT 의 is_anonymous 가 true). 게스트도 방에 들어가 함께 수정할 수 있지만 저장은 못 함.
create or replace function public.is_guest()
returns boolean language sql stable set search_path = public as $$
  select coalesce((auth.jwt() ->> 'is_anonymous')::boolean, true)
$$;

-- 방을 내 관계도로 저장(처음 저장한 사람이 주인). 다른 사람이 이미 저장한 방은 저장할 수 없음. 이름만 바꿀 때도 사용
create or replace function public.save_room(p_room text, p_title text)
returns boolean language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_owner uuid;
begin
  if not public.is_member(p_room) then raise exception 'not a member' using errcode = '42501'; end if;
  if public.is_guest() then raise exception 'login required' using errcode = '42501'; end if;
  select owner into v_owner from public.rooms where id = p_room for update;
  if v_owner is not null and v_owner <> v_uid then raise exception 'not owner' using errcode = '42501'; end if;
  update public.rooms
     set owner = v_uid, saved_at = now(), title = left(coalesce(nullif(btrim(p_title), ''), '이름 없는 관계도'), 100)
   where id = p_room;
  return true;
end $$;

-- 내가 저장한 관계도 목록 (최근 저장 순)
create or replace function public.my_rooms()
returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', r.id, 'title', r.title, 'saved_at', r.saved_at) order by r.saved_at desc), '[]'::jsonb)
    from public.rooms r where r.owner = auth.uid()
$$;

revoke execute on function public.join_room(text), public.apply_ops(text, jsonb), public.seed_room(text),
                           public.save_room(text, text), public.my_rooms() from public, anon;
grant  execute on function public.join_room(text), public.apply_ops(text, jsonb), public.seed_room(text),
                           public.save_room(text, text), public.my_rooms() to authenticated;

-- ---- Realtime: items 변경을 실시간으로 전달 ---------------------------------------
alter table public.items replica identity full;
do $$
begin
  if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'items') then
    alter publication supabase_realtime add table public.items;
  end if;
end $$;
