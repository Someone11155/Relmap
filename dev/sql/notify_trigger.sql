-- 가짜 Realtime 용: items 가 바뀌면 NOTIFY (실제 Supabase 에서는 Realtime 이 이 역할을 함)
create function public.__notify() returns trigger language plpgsql as $$
declare p text := json_build_object('room',new.room,'kind',new.kind,'id',new.id,'data',new.data,'deleted',new.deleted,'ver',new.ver)::text;
begin
  if length(p) > 7000 then p := json_build_object('room',new.room,'kind',new.kind,'id',new.id,'trunc',true)::text; end if;
  perform pg_notify('items', p); return new;
end $$;
create trigger items_notify after insert or update on public.items for each row execute function public.__notify();
