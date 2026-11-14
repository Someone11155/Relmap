# 인물 관계도 (relmap)

브라우저에서 인물·관계(화살표)·그룹을 그리는 편집기. 여러 명이 같은 방에서 **실시간 공동 편집**(Supabase)하고, JSON으로 저장·불러오기를 한다.

## 사용자와 작업 방식
- 사용자는 개발자가 아니라 **취미로 개발하는 학생**이고 코드를 직접 읽지 않는다. 한국어로, 무엇을 왜 바꿨는지 쉬운 말로 설명한다.
- 코드를 바꾸면 **직접 돌려서 확인**하고(`dev/run.sh`), 확인한 것과 못 한 것을 구분해서 보고한다. (실제 Supabase·모바일 기기는 이 환경에서 검증되지 않았음)
- 외부 라이브러리는 **릴리스 후 2주 이상 지난 버전을 정확히 고정**한다. 현재: `@supabase/supabase-js@2.118.0`(jsDelivr `+esm`), Pretendard 1.3.9, Cloudflare Turnstile(`api.js?render=explicit`).
- 가이드를 따를 때 기능·정책은 추측하지 말고 공식 문서를 확인한다.

## 파일
- `index.html` — 앱 전부(HTML+CSS+JS 한 파일, 빌드 없음). 배포할 땐 `index.html` + `config.js` 를 같은 폴더에서 함께 올린다.
- `config.js` — `window.RELMAP={SB_URL,SB_KEY,TS_KEY}`. 값은 **공개돼도 되는 것만**(Supabase publishable/anon 키, Turnstile *사이트* 키). 템플릿은 비어 있음. `index.html` 안 `CFG` 가 읽는다.
- `supabase_schema.sql` — Supabase SQL Editor 에서 실행하는 스키마(표, RLS, 함수 `join_room`/`seed_room`/`apply_ops`, Realtime 등록).
- `README.md` — 사용자용 설정·배포 순서. @README.md
- `dev/` — 테스트 환경. @dev/README.md

## index.html 지도 (주석으로 grep)
- `/* 화면 */` 줌·이동·`fit()`·`drawLinks()`(SVG 선 + `.lb` 라벨, 같은 쌍 여러 선은 평행 배치), `ovCheck()`(인물 글자와 겹친 라벨 반투명)
- `/* 포인터 */` 선택·드래그. 패널은 **클릭(움직임 4px 이하)일 때만** 열림(`select(id,true)` 로 조용히 선택 → pointerup 에서 `panel()`)
- `/* 물리 … */` `tick()`·`relax()`·`heat()`. **방 안에서는 자동 물리 없음**, `↻` 를 누른 사람 화면에서만 계산해 결과가 동기화됨
- `/* 실행 취소·다시 실행 … */` **혼자 쓸 때** 전용 스냅샷 방식(`snap`/`goH`)
- `/* 저장 / 불러오기 */` + `/* 데이터 검증 … */` `cleanEnt`/`cleanDoc`/`idOk`, JSON 저장·불러오기
- `/* 공동 편집 (Supabase) … */` 설정 상수, 그리고 하위 구역:
  `접속자 · 커서` / `문서 동기화`(`view`·`diff`·`enqueue`·`pump`·`ingestMany`·`recon`·`setLocal`·`dropLocal`) / `실행 취소 / 다시 실행 (사용자별, 직접 구현)`(`hrec`·`hclose`·`histMove`·제스처 `CB.gs/ge`) / `방 입장`(`enter`·`captcha`·`adopt`) / `연결 유지`(`rebuild`·`wake`)

데이터: `S={view,ph,nodes[],links[]}`. 노드 `t`='p'(인물)|'t'(텍스트)|'c'(그룹 원). 서버 표 `items(room,kind('n'|'l'),id,data jsonb,deleted,ver)`; `data` 는 id 를 뺀 필드 묶음.

## 핵심 설계와 이유 (바꾸기 전에 읽을 것)
1. **동기화 = base + 대기열(rebase)**. 화면 값 = 서버 확정 상태(`base`) 위에 보내는 중(`fl`)·보낼 예정(`qd`) 변경을 겹친 것(`view()`). `diff()` 가 `sh`(마지막 동기화 상태)와 비교해 필드 단위 변경을 만든다. 서버 응답/이벤트의 `ver`(단조 증가, **항상 `Number`로 비교** — 문자열이면 "4">"10" 오판)가 더 작으면 무시. 응답을 받은 뒤엔 해당 항목을 반드시 `recon` 한다(안 하면 동시 수정 시 영구히 갈라짐 — 실제로 겪은 버그).
2. **삭제는 `deleted=true` 표시**(Realtime 의 DELETE 이벤트는 방별 필터·RLS 가 안 됨). 되살리기는 `put`.
3. **키 순서가 다른 같은 객체**를 비교할 땐 `eq()`(깊은 비교) 사용. `JSON.stringify` 비교 금지(jsonb 는 키 순서가 달라짐).
4. **실행 취소(방 안)**: 항목별 `{이전,이후}` 를 기록하고, 되돌릴 땐 *내가 바꾼 필드만* 되돌려 남의 변경을 보존. 드래그·패널 입력·정렬 같은 제스처는 끝날 때까지 한 칸. 방 안에선 `초기화` 비활성, 불러오기는 확인창 후 한 덩어리로 기록(되돌리기 가능).
5. **보안 모델**: 방 주소 = 열쇠. 익명 로그인 + `join_room` 입장 등록 + RLS(표 직접 접근 불가, 함수로만 쓰기). **방에서 오는 값과 불러온 파일은 신뢰하지 않는다**: 반드시 `cleanEnt`/`cleanDoc` 를 거치고(색은 hex 만, 그림은 `data:image/` 만, id 는 `/^[A-Za-z0-9_-]{1,64}$/` 이고 `Object.prototype` 키 제외), HTML 문자열에 값을 넣을 땐 `esc()`. 과거에 관계선 색상으로 스크립트가 실행되는 XSS 가 있었고 고쳤다 — 새 필드를 추가하면 `cleanEnt` 와 렌더링 양쪽을 같이 수정할 것. `els`/`lels` 는 일반 객체라 키 접근 시 `Object.hasOwn`.
6. **재연결**: 서버가 채널을 닫으면(`CLOSED`) 라이브러리는 자동 재연결하지 않음 → `rebuild()` 로 새 채널을 만든다. 10초 넘게 백그라운드였다 돌아오면 새로 연결 + 전체 재조회(`wake`). 내 변경은 HTTP(`apply_ops`)로 보내므로 연결이 끊겨도 재시도된다.
7. **캡차**: Supabase 에서 CAPTCHA 를 켠 경우 익명 로그인에 토큰이 필요 → `TS_KEY` 가 있으면 Turnstile 로 확인 후 `signInAnonymously({options:{captchaToken}})`. 위젯의 Hostname 목록에 배포 주소를 등록해야 함.
8. **디자인**: 원티드 Montage 토큰(강조색 `#0066FF`, 중립 회색, 모서리 8/10/12/16px, 안쪽 1px 라인), Pretendard, Lucide 선 아이콘(스프라이트 `<symbol id="i-…">`), 라이트/다크 `:root` 변수.

## 알려진 한계 / 남은 일
- **읽기 전용 링크(권한 구분) 없음** — 방 주소를 아는 사람은 누구나 편집 가능.
- 값 검증이 **클라이언트에만** 있다(서버 DB 에는 검증 전 값이 저장될 수 있음). SQL 쪽 검사 추가 가능.
- 삭제 표시 행이 쌓임(정리 없음). 익명 로그인은 악용 위험이 있어 필요 시 캡차를 켠다.
- 혼자 쓸 때의 실행 취소는 스냅샷 방식이라, 물리가 움직이는 약 12초 동안은 한 번에 물리 한 프레임씩 되돌아감(원본 파일에서도 동일). 방 안의 새 방식을 혼자 쓸 때도 적용하면 해결됨.
- **실제 Supabase(익명 로그인·Realtime)와 모바일 실기기에서의 end-to-end 검증은 안 됨.** 가짜 서버 테스트만 통과.
- 이전에 쓰던 Liveblocks 는 완전히 제거됨(프로젝트도 삭제 가능).

## 테스트
`dev/run.sh` (전체) 또는 `dev/run.sh collab panel`. 기대 결과는 `dev/README.md` 표. 동기화·재연결·검증 코드를 바꾼 뒤엔 최소 `collab race json reconnect` 를 돌릴 것.

## 배포 메모
Cloudflare Pages(Direct Upload, 드래그 앤 드롭). **새 배포마다 폴더 전체를 다시 올려야 함**(`index.html`+`config.js`). 사용자의 프로젝트 이름은 `relationmap-2qa` (`relationmap-2qa.pages.dev`)일 수 있으니 확인할 것. 내 도메인은 서브도메인 CNAME 연결 권장.
