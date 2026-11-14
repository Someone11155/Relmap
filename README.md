# 인물 관계도 — 설정과 배포

## 1. Supabase 준비 (한 번만)
1. supabase.com 에서 프로젝트를 만든다.
2. **SQL Editor** 에 `supabase_schema.sql` 전체를 붙여 넣고 실행 (`Success. No rows returned`).
   - `DROP` 경고가 뜨는 것은 정상(같은 이름의 접근 규칙을 지우고 다시 만드는 줄). 단, 이 프로젝트에 이미 `rooms`, `room_members`, `items` 표가 있다면 먼저 `select table_name from information_schema.tables where table_schema='public';` 로 확인한다.
3. **Authentication → Sign In / Providers → Anonymous sign-ins** 켜기.
4. 프로젝트 URL 과 **publishable(anon) 키** 를 복사한다. (`secret`/`service_role` 키는 절대 사용 금지)

## 2. (선택) 캡차 — Supabase 에서 CAPTCHA 보호를 켠 경우
1. Cloudflare 대시보드 → Turnstile 에서 위젯 생성. **Hostname 목록에 접속 주소를 모두 등록**(`○○○.pages.dev`, 내 도메인).
2. Supabase → Authentication → (Bot and Abuse Protection) → CAPTCHA 켜고 제공자 **Turnstile**, **비밀 키(Secret key)** 입력.
3. Turnstile **사이트 키** 를 `config.js` 의 `TS_KEY` 에 넣는다. (캡차를 끄면 `TS_KEY` 는 비워도 됨)

## 3. config.js 채우기
```js
window.RELMAP = { SB_URL:'https://xxxx.supabase.co', SB_KEY:'sb_publishable_…', TS_KEY:'0x…' };
```
공개돼도 되는 값만 넣는다.

## 4. Cloudflare Pages 에 올리기
- 폴더 하나에 `index.html` 과 `config.js` 를 넣는다.
- 대시보드 **Workers & Pages → Create application → Get started → Drag and drop your files** → 프로젝트 이름 → 폴더를 끌어다 놓고 **Deploy site**.
- **수정 후 다시 올리기**: 프로젝트에서 **Create a new deployment** → Production → **폴더 전체**(두 파일 모두)를 다시 올린다. 값이 채워진 `config.js` 는 따로 보관.
- 내 도메인: 프로젝트 **Custom domains → Set up a domain**. 먼저 Pages 에 등록한 뒤 DNS 에 `CNAME relmap → <프로젝트>.pages.dev` 를 추가(서브도메인 권장). Turnstile Hostname 에도 추가.

## 5. 사용
- `공동 편집` → 주소 뒤에 `#room=…` 이 붙는다. 그 주소를 믿을 만한 사람에게만 공유(주소 = 열쇠).
- 툴바 `저장`/`불러오기` = JSON. 공동 편집 중 불러오기는 방 전체가 바뀌며 `↶` 로 되돌릴 수 있다.

## 문제 해결
앱이 띄우는 안내창이 원인을 알려 준다: 익명 로그인 꺼짐 / SQL 미실행 / Realtime 꺼짐 / 키·URL 오류 / 캡차(TS_KEY·Hostname·비밀 키 불일치).
모바일에서 "다시 연결 중…" 이 오래 가면 브라우저와 지속 시간을 알려 주세요.
