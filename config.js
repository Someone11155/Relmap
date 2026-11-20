/* 인물 관계도 설정 — index.html 과 같은 폴더에 두고 함께 올리세요.
   아래 값들은 공개되어도 되는 값입니다. 반대로 Supabase 의 secret / service_role 키,
   Turnstile 의 비밀 키(Secret key)는 이 파일에 절대 넣지 마세요. */
window.RELMAP = {
  SB_URL: '',   // Supabase 프로젝트 URL      예: 'https://abcd1234.supabase.co'
  SB_KEY: '',   // Supabase publishable(anon) 키  예: 'sb_publishable_…'
  TS_KEY: '',   // Cloudflare Turnstile 사이트 키(Site key)  예: '0x4AAAA…'  ← Supabase 에서 CAPTCHA 를 켠 경우에만 필요
  PHOTO: '',    // 사진 서버(Cloudflare Worker) 주소  예: 'https://relmap-photos.내계정.workers.dev'  ← 비워 두면 사진을 문서 안에 넣음. 설정법은 worker/README.md
  REALTIME: ''  // 실시간 중계 서버(Cloudflare Durable Object) 주소  예: 'https://relmap-rt.내계정.workers.dev'  ← 비워 두면 Supabase Realtime 을 씀. 설정법은 worker/README.md
};
