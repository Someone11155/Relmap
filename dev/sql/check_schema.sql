\set ON_ERROR_STOP off
\echo '== 1. u1 입장 → seeded? (false 여야 함), 시드, 재시드(false)'
set role authenticated; set request.jwt.claim.sub='11111111-1111-1111-1111-111111111111';
select join_room('room-test-0001') as seeded_before;
select seed_room('room-test-0001') as first_seed_true;
select apply_ops('room-test-0001','[{"k":"n","id":"a","put":{"t":"p","x":1,"y":2,"name":"A","pin":true}},{"k":"n","id":"b","put":{"t":"p","x":5,"y":6,"name":"B"}},{"k":"l","id":"l1","put":{"a":"a","b":"b","label":"x"}}]'::jsonb) is not null as uploaded;
select seed_room('room-test-0001') as second_seed_should_be_false;
select kind,id,data,deleted from items where room='room-test-0001' order by kind,id;

\echo '== 2. u2: 입장 전에는 안 보임 / apply 불가, 입장 후 보임'
set request.jwt.claim.sub='22222222-2222-2222-2222-222222222222';
select count(*) as rows_visible_before_join from items;
select apply_ops('room-test-0001','[{"k":"n","id":"a","set":{"x":9}}]'::jsonb);
select join_room('room-test-0001') as seeded_for_u2_should_be_true;
select count(*) as rows_visible_after_join from items;

\echo '== 3. 필드 단위 병합: u1 이 x,y 변경 / u2 가 name 변경 / pin 제거 → 서로의 변경 유지'
set request.jwt.claim.sub='11111111-1111-1111-1111-111111111111';
select jsonb_pretty(apply_ops('room-test-0001','[{"k":"n","id":"a","set":{"x":100,"y":200}}]'::jsonb));
set request.jwt.claim.sub='22222222-2222-2222-2222-222222222222';
select apply_ops('room-test-0001','[{"k":"n","id":"a","set":{"name":"A2"},"rm":["pin"]}]'::jsonb);
select data, ver from items where id='a';

\echo '== 4. 삭제 → 삭제된 것에 set 은 무시 → put 으로 되살리기 / 같은 호출 안 여러 op 순서대로'
select apply_ops('room-test-0001','[{"k":"n","id":"b","del":true}]'::jsonb);
select apply_ops('room-test-0001','[{"k":"n","id":"b","set":{"x":777}}]'::jsonb);
select id,data,deleted from items where id='b';
select apply_ops('room-test-0001','[{"k":"n","id":"b","put":{"t":"p","x":1,"name":"B again"}},{"k":"n","id":"b","set":{"y":2}}]'::jsonb);

\echo '== 5. 비정상 입력 / 권한'
select join_room('bad id!');
select apply_ops('room-test-0001','[{"k":"x","id":"q","put":{}}]'::jsonb);
select apply_ops('room-test-0001','[{"k":"n","id":"q","put":[1,2]}]'::jsonb);
insert into items(room,kind,id) values ('room-test-0001','n','hack');
update items set data='{}' where id='a';
delete from items where id='a';
select * from rooms;
select * from room_members;

\echo '== 6. 방 격리: u3 는 아무것도 못 봄 / 다른 방 id 로 apply 불가'
set request.jwt.claim.sub='33333333-3333-3333-3333-333333333333';
select count(*) as u3_rows from items;
select apply_ops('room-test-0001','[{"k":"n","id":"a","set":{"x":0}}]'::jsonb);
select join_room('room-test-0002');
select count(*) as u3_rows_in_other_room from items;
select apply_ops('room-test-0002','[{"k":"n","id":"a","put":{"t":"p"}}]'::jsonb) is not null as ok_own_room;

\echo '== 7. 익명(anon) 역할은 함수 실행/표 읽기 불가'
reset role; set role anon; set request.jwt.claim.sub='';
select join_room('room-test-0003');
select * from items;
reset role;
select 'ver 는 단조 증가:' , (select count(*)=count(distinct ver) from items) as all_distinct;
