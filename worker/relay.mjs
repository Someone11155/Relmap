// 방 하나의 실시간 중계 규칙(순수 로직). Cloudflare Durable Object(rt.mjs)와 테스트용 가짜 서버(dev/fakesb.mjs)가 같은 코드를 씀.
// 앱(index.html 의 RtChan)과 주고받는 글(JSON 한 줄):
//   앱→서버  {t:'auth',token}            로그인 확인(Supabase 토큰). 통과하기 전에는 다른 건 전부 무시
//            {t:'b',e:'cur'|'rows',p}    같은 방 다른 사람들에게 그대로 전달(커서·문서 변경)
//            {t:'track',p,id}            내 접속자 정보(이름·색·선택) 등록 → 모두에게 접속자 목록을 다시 보냄, 나에게 ack
//            {t:'untrack'}               내 접속자 정보 지움
//            'ping'                      살아 있는지 확인 → 'pong'(Durable Object 는 깨우지 않고 자동으로 답함)
//   서버→앱  {t:'hello'} {t:'pres',s:{키:정보}} {t:'b',e,p} {t:'ack',id}
// peer = 소켓을 감싼 것 {id, send(글), close(코드), get() → {k,ok,p}, set(값)}
// shortcut: 소켓별 속도 제한 없음(글 크기만 제한) — 로그인한 사용자가 마구 보내면 Cloudflare 무료 요청 한도를 쓸 수 있음, 그런 일이 보이면 제한을 넣을 것
const OUT = ['cur', 'rows'], MAX = 300_000;
const pres = peers => Object.fromEntries(peers.filter(q => q.get().ok && q.get().p).map(q => [q.get().k, q.get().p]));
const sendPres = peers => { const s = JSON.stringify({ t: 'pres', s: pres(peers) }); peers.forEach(q => q.get().ok && q.send(s)) };
export async function onMessage(peers, me, raw, verify) {
  if (typeof raw != 'string' || raw.length > MAX) return;
  if (raw == 'ping') return me.send('pong');
  let m; try { m = JSON.parse(raw) } catch { return }
  if (!m || typeof m != 'object') return;
  const a = me.get();
  if (!a.ok) {   // 로그인 확인 전에는 auth 만 받음
    if (m.t != 'auth' || typeof m.token != 'string' || !(await verify(m.token).catch(() => false))) return me.close(4401);
    me.set({ ...a, ok: true }); me.send('{"t":"hello"}'); return sendPres(peers);
  }
  if (m.t == 'b' && OUT.includes(m.e)) { const s = JSON.stringify({ t: 'b', e: m.e, p: m.p }); peers.forEach(q => q.id !== me.id && q.get().ok && q.send(s)); return }
  if (m.t == 'track') {
    if (m.p && typeof m.p == 'object' && !Array.isArray(m.p) && JSON.stringify(m.p).length < 2000) { me.set({ ...a, p: m.p }); sendPres(peers) }
    if (m.id != null) me.send(JSON.stringify({ t: 'ack', id: m.id }));
    return;
  }
  if (m.t == 'untrack') { const { p, ...r } = a; me.set(r); sendPres(peers) }
}
// 연결이 끊긴 뒤: 남은 사람들에게 접속자 목록을 다시 보냄(peers 는 끊긴 사람을 빼고 넘김)
export const onLeave = (peers, me) => sendPres(peers.filter(q => q.id !== me.id));
