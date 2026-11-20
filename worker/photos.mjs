// 사진 서버(Cloudflare Worker + R2). 설정 방법은 worker/README.md
//   PUT /          로그인(게스트 포함)한 사람이 JPEG 를 올림 → {url} 로 돌려줌. 파일 이름 = 내용의 SHA-256, 같은 사진은 한 번만 저장됨
//   GET /<해시>.jpg  누구나 볼 수 있고 브라우저가 1년 동안 저장해 둠(내용이 바뀌지 않는 이름이라 안전)
// 필요한 설정: R2 바인딩 이름 R2, 변수 SB_URL(Supabase 프로젝트 URL), SB_KEY(publishable 키) — 둘 다 공개돼도 되는 값
// shortcut: 한 사람이 올리는 양을 제한하지 않음(크기만 제한), 악용이 보이면 사용자별 횟수 제한을 넣을 것. CORS 는 전체 허용(올리기는 토큰이 있어야 함)
const MAX = 300_000, CORS = { 'access-control-allow-origin': '*', 'access-control-allow-headers': 'authorization,content-type', 'access-control-allow-methods': 'GET,PUT,OPTIONS' };
export default {
  async fetch(req, env) {
    const u = new URL(req.url), res = (b, s = 200, h = {}) => new Response(b, { status: s, headers: { ...CORS, ...h } });
    if (req.method == 'OPTIONS') return res(null, 204);
    if (req.method == 'GET') {
      const m = u.pathname.match(/^\/([0-9a-f]{64}\.jpg)$/), o = m && await env.R2.get(m[1]);
      return o ? res(o.body, 200, { 'content-type': 'image/jpeg', 'cache-control': 'public, max-age=31536000, immutable' }) : res('not found', 404);
    }
    if (req.method != 'PUT' || u.pathname != '/') return res('method', 405);
    if (+req.headers.get('content-length') > MAX) return res('size', 413);
    // 로그인 확인: Supabase 가 토큰을 검사해 주므로 비밀 키가 필요 없음
    const a = await fetch(env.SB_URL + '/auth/v1/user', { headers: { authorization: req.headers.get('authorization') || '', apikey: env.SB_KEY } });
    if (!a.ok) return res('login', 401);
    const buf = await req.arrayBuffer();
    if (!buf.byteLength || buf.byteLength > MAX) return res('size', 413);
    const b = new Uint8Array(buf);
    if (b[0] != 0xff || b[1] != 0xd8 || b[2] != 0xff) return res('type', 415);   // JPEG 만(앱이 올리기 전에 항상 JPEG 로 줄임)
    const key = [...new Uint8Array(await crypto.subtle.digest('SHA-256', buf))].map(x => x.toString(16).padStart(2, '0')).join('') + '.jpg';
    if (!await env.R2.head(key)) await env.R2.put(key, buf, { httpMetadata: { contentType: 'image/jpeg' } });
    return res(JSON.stringify({ url: u.origin + '/' + key }), 200, { 'content-type': 'application/json' });
  }
};
