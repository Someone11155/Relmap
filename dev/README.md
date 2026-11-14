# 테스트 환경 (dev/)

실제 Supabase 프로젝트 없이도 앱의 동기화·공동 편집 동작을 검증하기 위한 환경입니다.

## 구성
- `fakesb.mjs` — 가짜 Supabase 서버. **진짜 SQL 함수(`../supabase_schema.sql`)를 Postgres 에서 그대로 실행**하고, PostgREST·Realtime(Postgres Changes)·Broadcast·Presence 의 겉모습만 흉내냅니다(8790 포트).
- `stubs/client_stub.js`, `client_stub_cap.js` — 브라우저의 `supabase-js` 를 대신하는 흉내 클라이언트(테스트가 CDN 요청을 가로채 이 파일로 대체). `_cap` 은 캡차 필수 환경 흉내.
- `sql/` — 테스트 DB 준비용 SQL(`env.sql`: 역할·auth.uid() 흉내, `notify_trigger.sql`: 변경 알림), `check_schema.sql`(스키마를 눈으로 확인하는 시나리오).
- `tests/` — Playwright(Python) 테스트. `helpers.py` 가 공통 도구.
- `run.sh` — DB 준비 → 서버 두 개 실행 → 테스트 → 정리를 한 번에.

## 필요한 것
- Node 18+ , Python 3.9+ , `psql` 클라이언트 , Postgres 14+ (슈퍼유저로 TCP 접속 가능해야 함)
- `cd dev && npm install` (pg 설치)
- `pip install playwright && playwright install chromium`
- Postgres 가 없다면 Docker 로: `docker run --name relmap-pg -e POSTGRES_PASSWORD=pw -p 5432:5432 -d postgres:16`
- 접속 정보 기본값: `127.0.0.1:5432` 사용자 `postgres` 비밀번호 `pw` (환경변수 `PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE` 로 변경)
- 스크립트가 bash 입니다. Windows 는 Git Bash 또는 WSL 에서 실행하세요.

## 실행
```
dev/run.sh                 # 전체 (몇 분 걸림)
dev/run.sh collab panel    # 일부만
```
테스트는 `http://localhost:8765/index.html?mode=edit`(프로젝트 루트를 서빙)을 브라우저로 열어 실제 앱을 조작합니다. 앱은 기본이 읽기 모드라서 `?mode=edit` 로 편집 모드로 시작시킵니다(`mode` 테스트만 주소 뒤에 아무것도 안 붙인 경우도 확인).

## 테스트 목록과 기대 결과
| 이름 | 무엇을 검증하나 | 기대 |
|---|---|---|
| panel | 클릭 때만 설정 패널이 뜨고 드래그 중엔 안 뜸 | PASS 13 |
| overlap | 인물 글자와 겹친 관계선 글자 반투명 | PASS 7 |
| mode | 읽기(기본)·편집·이동 모드 동작, 우클릭 드래그 화면 이동, 방 안 읽기 모드, 드래그(마우스·터치) 중 프로필이 안 뜸, 편집용 링크 복사(감상용 버튼 없음)·예전 감상용 링크는 읽기 모드 | PASS 33 |
| phys | 읽기 모드 물리(화면 전용·선 길이 일정·범위 제한·놓으면 복귀·그룹 원이 따라감·큰 그래프 안정) + 편집 모드 물리 꺼짐 | PASS 14 |
| works | 작품(영화·드라마·에피소드 수) 목록, 인물·선 태그(체크·중간 상태·정리), 읽기 모드 표시, 잘못된 값 걸러내기, JSON 왕복, 방 동기화·실행 취소 | PASS 19 |
| watch | 에피소드 이름, 읽기 모드 '본 작품' 선택과 안 본 작품(인물·선·그룹) 숨김, 프로필에 안 새는지, 새로고침 유지, 편집 모드는 전부 보임, 인물의 시청에 따라 보이는 추가 설명(추가·조건 선택·읽기 모드 숨김·삭제·잘못된 값 거름·방 동기화), 방 안 각자 다른 화면 | PASS 29 |
| auth | 게스트는 저장 불가(서버가 거부·화면은 로그인 안내)·방 기여는 가능, 로그인(이메일+비밀번호 로그인, 별도 가입 화면(비밀번호 재입력 확인)·비밀번호 찾기·Google 요청, Apple 없음), 서버 저장·내 관계도 목록·남의 방 가로채기 불가, 백업/감상용 파일, 감상용 파일 읽기 고정, 로그아웃, 상단바 창이 버튼 아래 드롭다운으로 뜸 | PASS 31 |
| backup | 자동 백업(열 때 보관·5분 규칙·초기화 직전 보관·복원·목록 드롭다운·새로고침 유지), 그룹 원 배경 이미지(첨부·제거·잘못된 값 거름·방 동기화) | PASS 13 |
| multi | 편집 모드 사각형 다중 선택(선택·함께 이동·삭제·실행 취소·단일 선택·해제), 방 안 삭제·되돌리기 동기화 | PASS 10 |
| collab | 방 생성·입장·드래그·동시 수정·삭제/실행 취소·커서·재접속 복구·영속성 | PASS 16 |
| captcha | Turnstile 증표 전달, 설정 오류 안내, config.js 처리 | PASS 10 |
| reconnect | 채널 닫힘·오류·백그라운드 복귀·네트워크 복귀 시 자동 재연결 | PASS 12 |
| race | 같은 필드 동시 수정 40회가 모두 같은 값으로 수렴 | `diverged 0 / 40` |
| json | JSON 저장·불러오기(혼자/방 안), 악의적 값 방어(XSS 포함) | PASS 23 |
| stress | 무작위 지연·여러 필드 동시 수정 30라운드 수렴 (선택, `run.sh stress`) | `diverged 0/30` |

## 한계 (중요)
- 가짜 서버는 **실제 Supabase 의 로그인(익명 로그인·캡차)과 Realtime 전달을 흉내**만 냅니다. 이 부분과 실제 모바일 기기 동작은 테스트로 검증되지 않았으니, 배포 환경에서 직접 확인해야 합니다.
- 테스트의 일부(재연결·시간 관련)는 몇 초씩 기다리므로 느린 컴퓨터에서는 간격을 늘려야 할 수 있습니다.
