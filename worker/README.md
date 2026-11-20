# 사진 서버 설정 (Cloudflare Worker + R2)

`photos.mjs` 는 사진을 R2 에 저장하고 주소를 돌려주는 작은 서버입니다. 대시보드에서 코드를 붙여 넣기만 하면 되고 따로 설치할 것은 없습니다.
(Pages 의 끌어다 놓기 배포는 `functions` 폴더를 지원하지 않아서 Pages 안이 아니라 **별도의 Worker** 로 만듭니다.)

## 만들기 (한 번만)
1. Cloudflare 대시보드 → **R2 Object Storage** → **Create bucket** → 이름 `relmap-photos`.
   - R2 를 처음 켤 때 결제 수단 등록을 요구할 수 있어요(무료 한도 — 저장 10GB, 읽기 월 1천만 회, 쓰기 월 100만 회 — 안에서는 청구되지 않아요. 전송량(egress)은 무료예요).
2. **Workers & Pages** → **Create** → **Create Worker** → 이름 `relmap-photos` → **Deploy** → **Edit code**.
   `photos.mjs` 의 내용을 전부 복사해 기존 코드를 지우고 붙여 넣은 뒤 **Deploy**.
3. 이 Worker 의 **Settings → Bindings → Add → R2 bucket**: 변수 이름 `R2`, 버킷 `relmap-photos`. (화면 이름은 조금 다를 수 있어요.)
4. **Settings → Variables and Secrets** 에 일반 텍스트(Text)로 두 개 추가:
   - `SB_URL` = Supabase 프로젝트 URL (`https://….supabase.co`)
   - `SB_KEY` = Supabase **publishable(anon)** 키 — 공개돼도 되는 값이에요. **secret / service_role 키는 절대 넣지 마세요.**
5. Worker 의 주소(`https://relmap-photos.내계정.workers.dev`)를 `config.js` 의 `PHOTO` 에 적고, `index.html` 과 `config.js` 를 같은 폴더에서 Pages 에 **다시 올립니다**.

### 2~4번을 명령줄로 한 번에 하려면 (실시간 중계 서버와 같은 Wrangler)
1번(R2 버킷 `relmap-photos` 만들기)은 대시보드에서 먼저 하고, `worker` 폴더에서(`npx wrangler login` 은 한 번만):
`npx wrangler deploy -c wrangler.photos.toml` — Worker 만들기·코드·R2 연결·변수(`SB_URL`·`SB_KEY`, `wrangler.photos.toml` 에 적힌 값)가 한 번에 되고, 끝에 나오는 주소를 5번처럼 `PHOTO` 에 적어요. 같은 이름의 Worker 를 대시보드로 이미 만들었다면 그 위에 덮어써요(변수는 이 파일 값으로 바뀜).

## 확인
- 공동 편집 방에서 인물이나 그룹에 사진을 붙인 뒤, 서버 DB 에는 `https://…workers.dev/<긴 영문숫자>.jpg` 주소만 들어 있어야 해요.
- 이미 문서 안에 들어 있는 예전 사진은 편집 모드에서 **링크 공유 창 → "사진 서버로 옮기기"** 를 누르면 옮겨져요. 옮긴 뒤 방에 있던 사람들은 **새로고침**하세요(옛 버전 화면은 새 주소 사진을 못 봐요).

## 알아둘 점
- **주소를 바꾸지 마세요.** 앱은 `PHOTO` 로 시작하는 주소의 사진만 보여 줘요. Worker 이름이나 주소를 바꾸면 기존 사진이 안 보이게 돼요.
- 올릴 수 있는 사람은 앱에 접속한(게스트 포함) 사용자예요. 크기(300KB)·형식(JPEG)만 제한하고, 한 사람이 올리는 양은 제한하지 않아요. 이상한 사용이 보이면 제한을 넣어야 해요.
- 파일로 저장(백업·감상용)하면 사진은 서버 주소가 아니라 사진 자체로 들어가요. 그래서 파일 하나로 완결되고, 저장하는 데 시간이 조금 더 걸릴 수 있어요.
- 혼자 쓸 때(공동 편집 방 밖)는 사진 서버를 쓰지 않고 예전처럼 문서 안에 넣어요.

---

# 실시간 중계 서버 설정 (Cloudflare Durable Object)

커서·접속자·문서 변경을 주고받는 일을 Supabase Realtime 대신 이 서버가 맡습니다(Supabase 무료 실시간 메시지는 월 200만 개). 문서 저장과 로그인은 그대로 Supabase 입니다.
`rt.mjs`(껍데기)·`relay.mjs`(규칙)·`wrangler.toml`(설정) 세 파일을 씁니다. 사진 서버와 달리 **Wrangler(명령줄 도구)로 배포**해요 — Durable Object 는 공식 문서의 안내가 Wrangler 기준이에요.

## 만들기 (한 번만)
1. **Node.js** 를 설치해요(https://nodejs.org 의 LTS 버전).
2. 터미널(Windows 는 PowerShell)을 열고 이 프로젝트의 `worker` 폴더로 이동해요. 예: `cd C:\Users\내이름\Downloads\relmap-handoff\worker`
3. `npx wrangler login` — 브라우저가 열리면 Cloudflare 에 로그인하고 허용해요. (비밀번호나 키를 파일에 적을 필요는 없어요.)
4. `wrangler.toml` 을 열어 맨 아래 `SB_URL`(Supabase 프로젝트 URL)과 `SB_KEY`(**publishable(anon) 키**)를 채워요. 공개돼도 되는 값이에요. **secret / service_role 키는 절대 넣지 마세요.**
5. `npx wrangler deploy` — 끝에 `https://relmap-rt.내계정.workers.dev` 같은 주소가 나와요.
6. 그 주소를 브라우저로 열어서 `relmap realtime relay` 라는 글이 보이면 배포가 된 거예요.
7. 그 주소를 `config.js` 의 `REALTIME` 에 적고, `index.html` 과 `config.js` 를 같은 폴더에서 Pages 에 **다시 올려요.**

## 확인
- 공동 편집 방에 두 명이 들어가서 서로의 커서·접속자 표시가 보이고, 한쪽이 인물을 옮기면 다른 쪽에 바로 따라오면 돼요.
- Supabase 대시보드 Usage 의 **Realtime Messages** 가 더 이상 늘지 않아야 해요(하루 이틀 뒤 확인).
- "실시간 중계 서버에 연결하지 못했습니다" 안내가 뜨면: `config.js` 의 주소 오타, Worker 배포 여부, `wrangler.toml` 의 `SB_URL`·`SB_KEY` 값을 확인하세요.

## 알아둘 점
- 무료 한도: Durable Object 요청 하루 10만(WebSocket 연결 1회가 1, 들어오는 메시지 20개가 1, 나가는 메시지는 무료). 이 서버는 아무것도 저장하지 않아요.
- 로그인(게스트 포함)한 사용자가 방 이름을 알면 접속할 수 있어요(방 주소 = 열쇠와 같은 수준). 한 사람이 보내는 양을 제한하지는 않아요.
- 설정(`REALTIME`)을 지우면 앱은 예전처럼 Supabase Realtime 을 써요.
- Cloudflare 에서 실제로 돌려 본 것은 아니에요(가짜 서버 테스트만 통과). 배포 뒤 위 "확인"을 꼭 해 보세요.
