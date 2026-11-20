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

## 2-1. 로그인(저장 기능을 쓰려면) — 게스트와 로그인 혼용
- **게스트**(로그인 안 함): 공유받은 방에 들어가 함께 수정할 수 있지만 **저장(서버·파일)은 못 해요.**
- **로그인한 사람**: 「저장」으로 서버에 저장(내 관계도 목록)하고 백업 파일·감상용 파일을 내려받을 수 있어요.
- 설정(Supabase 대시보드):
  1. `supabase_schema.sql` 을 **다시 한 번 통째로 실행**해요(저장용 열·함수가 추가돼요. 이미 있는 데이터는 그대로예요).
  2. **Authentication → URL Configuration** 의 **Site URL** 과 **Redirect URLs** 에 배포 주소(`https://○○○.pages.dev`, 내 도메인)를 넣어요. 로그인 링크는 여기 적힌 주소로만 돌아와요.
  3. **이메일 로그인**: 기본으로 켜져 있어요. 다만 Supabase 기본 메일 서버는 **프로젝트 팀원 주소에만, 시간당 2통**까지 보내요. 다른 사람이 쓰려면 직접 메일 서비스(SMTP)를 연결해야 해요.
     - Supabase 대시보드 → Authentication 의 **SMTP Settings**(주소: `https://supabase.com/dashboard/project/<프로젝트>/auth/smtp`)에서 Custom SMTP 를 켜고 **호스트·포트·사용자 이름·비밀번호·보내는 주소·보내는 사람 이름**을 넣고 저장해요. 공식 문서가 권하는 서비스: Resend, AWS SES, Postmark, SendGrid, ZeptoMail, Brevo.
     - 연결하면 아무 주소로나 보낼 수 있고, 기본 한도는 **시간당 30통**이에요(Authentication → Rate Limits 에서 조절).
     - 메일이 스팸함으로 가지 않으려면 메일 서비스에서 보내는 도메인의 SPF·DKIM·DMARC 설정을 해요(공식 문서 권장). SMTP 비밀번호는 Supabase 대시보드에만 넣고 `config.js` 등 파일에는 절대 넣지 마세요.
  4. **이메일+비밀번호 가입·로그인**: 기본으로 켜져 있어요(Authentication → Sign In / Providers → Email). 호스팅 프로젝트는 **Confirm email**(가입 확인 메일)이 기본 켜짐이라, 가입하면 확인 메일의 링크를 눌러야 로그인돼요(끄면 가입 즉시 로그인). 비밀번호 찾기 링크도 같은 메일 서버로 나가고 돌아올 주소는 위 Redirect URLs 에 있어야 해요. 비밀번호 최소 길이 등은 Supabase 쪽 설정을 따라요.
  5. **Google 로그인**: **Authentication → Sign In / Providers** 에서 켜고, Google Cloud 에서 받은 클라이언트 정보를 넣어요. 자세한 순서는 Supabase 공식 안내를 따르세요. 켜지 않으면 Google 버튼은 오류가 나요.
  6. 캡차를 켠 경우 이메일 로그인·가입·비밀번호 찾기 요청에도 같은 캡차 확인이 쓰여요(`TS_KEY`).
- 저장하지 않은 방(게스트가 만든 방)도 지금은 지워지지 않고 계속 남아요. 오래된 방을 정리하는 기능은 아직 없어요.

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

## 4-1. (선택, 권장) 사진 서버 — 사진을 Cloudflare R2 에 두기
- 사진이 서버 DB 행 안에 들어 있으면 방에 들어올 때마다 사진까지 내려받아 Supabase 의 데이터 전송량(egress) 무료 한도(월 5GB)를 빨리 씁니다. 사진을 R2(전송 요금 없음)에 두고 문서에는 주소만 넣으면 이 문제가 사라집니다.
- 설정은 `worker/README.md` 를 따라 하세요(Worker 하나와 R2 버킷 하나). 끝나면 `config.js` 의 `PHOTO` 에 Worker 주소를 적고 폴더를 다시 올립니다.
- 안 하면 예전처럼 사진이 문서 안에 들어갑니다(앱은 그대로 동작).

## 4-2. (선택, 권장) 실시간 중계 서버 — Supabase 실시간 메시지 한도 피하기
- Supabase 무료는 실시간 메시지가 월 200만 개라서 커서·접속자·변경을 계속 주고받으면 금방 찹니다. 이 부분만 Cloudflare 의 중계 서버(Durable Object)가 맡게 하면 Supabase 실시간 메시지를 쓰지 않습니다. 문서 저장과 로그인은 그대로 Supabase 입니다.
- 설정은 `worker/README.md` 의 "실시간 중계 서버" 를 따라 하세요(명령 몇 줄). 끝나면 `config.js` 의 `REALTIME` 에 주소를 적고 폴더를 다시 올립니다.
- 안 하면 예전처럼 Supabase Realtime 을 씁니다(앱은 그대로 동작).

## 5. 사용
- `공동 편집` → 주소 뒤에 `#room=…` 이 붙는다. 그 주소를 믿을 만한 사람에게만 공유(주소 = 열쇠).
- 툴바 `저장`: 서버 설정이 없으면 바로 JSON 파일로 저장. 설정이 있으면 로그인한 사람만 저장할 수 있고(서버 저장·백업 파일·감상용 파일), 감상용 파일을 `불러오기` 하면 읽기 모드만 쓸 수 있어요. `불러오기` = JSON. 공동 편집 중 불러오기는 방 전체가 바뀌며 `↶` 로 되돌릴 수 있다.

## 문제 해결
앱이 띄우는 안내창이 원인을 알려 준다: 익명 로그인 꺼짐 / SQL 미실행 / Realtime 꺼짐 / 키·URL 오류 / 캡차(TS_KEY·Hostname·비밀 키 불일치).
모바일에서 "다시 연결 중…" 이 오래 가면 브라우저와 지속 시간을 알려 주세요.
