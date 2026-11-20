// 실시간 중계 서버(Cloudflare Worker + Durable Object). 방마다 Durable Object 하나가 연결된 사람들 사이에서 커서·접속자·문서 변경을 전달함.
// 문서 저장과 로그인은 계속 Supabase 가 하고, 여기서는 아무것도 저장하지 않음. 규칙은 relay.mjs, 설정·배포는 worker/README.md
// 필요한 변수(wrangler.toml 의 [vars]): SB_URL(Supabase 프로젝트 URL), SB_KEY(publishable 키) — 둘 다 공개돼도 되는 값
import { DurableObject } from 'cloudflare:workers';
import { onMessage, onLeave } from './relay.mjs';

const wrap = ws => ({
  id: ws,
  send: s => { try { ws.send(s) } catch { } },
  close: c => { try { ws.close(c, 'auth') } catch { } },
  get: () => ws.deserializeAttachment() || {},
  set: v => ws.serializeAttachment(v),
});

export class Room extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    ctx.setWebSocketAutoResponse(new WebSocketRequestResponsePair('ping', 'pong'));   // 앱의 살아있음 확인에 Durable Object 를 깨우지 않고 답함
  }
  async fetch(req) {
    const k = new URL(req.url).searchParams.get('k') || '';
    if (!/^[\w-]{1,64}$/.test(k)) return new Response('bad key', { status: 400 });
    const [client, server] = Object.values(new WebSocketPair());
    this.ctx.acceptWebSocket(server);   // 쉬는 동안 메모리에서 내려가도 연결은 유지됨(Hibernation)
    server.serializeAttachment({ k });
    return new Response(null, { status: 101, webSocket: client });
  }
  peers() { return this.ctx.getWebSockets().map(wrap) }
  verify = t => fetch(this.env.SB_URL + '/auth/v1/user', { headers: { authorization: 'Bearer ' + t, apikey: this.env.SB_KEY } }).then(r => r.ok);   // Supabase 가 토큰을 검사해 줌 → 비밀 키 불필요
  async webSocketMessage(ws, msg) { await onMessage(this.peers(), wrap(ws), msg, this.verify) }
  async webSocketClose(ws) { try { ws.close(1000) } catch { } onLeave(this.peers(), wrap(ws)) }
  async webSocketError(ws) { onLeave(this.peers(), wrap(ws)) }
}

export default {
  async fetch(req, env) {
    const m = new URL(req.url).pathname.match(/^\/room\/([\w-]{8,64})$/);
    if (!m) return new Response('relmap realtime relay', { status: 200 });   // 브라우저로 열어 배포가 됐는지 확인용
    if (req.headers.get('Upgrade') != 'websocket') return new Response('expected websocket', { status: 426 });
    return env.ROOM.getByName(m[1]).fetch(req);
  }
};
