// Supabase 흉내 서버: 진짜 SQL 함수(Postgres)를 그대로 쓰고, PostgREST/Realtime 의 겉모습만 흉내냄
import http from 'http'; import pg from 'pg'; import {randomUUID} from 'crypto'; import photoWorker from '../worker/photos.mjs'; import {WebSocketServer} from 'ws'; import {onMessage,onLeave} from '../worker/relay.mjs';
const PGCFG={host:process.env.PGHOST||'127.0.0.1',port:+(process.env.PGPORT||5432),user:process.env.PGUSER||'postgres',password:process.env.PGPASSWORD||'pw',database:process.env.PGDATABASE||'relmap_test2'};
const pool=new pg.Pool({...PGCFG,max:10});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const cfg={delay:0,jitter:0,drop:{},confirm:false};   // confirm: 가입 확인 메일이 필요한 설정 흉내          // 이벤트 지연/유실 시뮬레이션
const subs=new Set(), presence=new Map(), mail=new Map(), who=new Map(), pws=new Map();   // mail: 이메일->uid, who: uid->이메일(로그인한 사용자)       // presence: room -> Map(key->payload)
async function asUser(uid,fn){const c=await pool.connect();try{await c.query('begin');await c.query('set local role authenticated');await c.query("select set_config('request.jwt.claim.sub',$1,true)",[uid]);await c.query("select set_config('request.jwt.claims',$1,true)",[JSON.stringify({sub:uid,is_anonymous:!who.has(uid)})]);const r=await fn(c);await c.query('commit');return r}catch(e){try{await c.query('rollback')}catch{}throw e}finally{c.release()}}
function send(sub,obj){sub.chain=sub.chain.then(async()=>{await sleep(cfg.delay+Math.random()*cfg.jitter);if(cfg.drop[sub.key])return;try{sub.res.write('data: '+JSON.stringify(obj)+'\n\n')}catch{}})}
const listener=new pg.Client(PGCFG);
await listener.connect();await listener.query('listen items');
listener.on('notification',async m=>{let row=JSON.parse(m.payload);
  if(row.trunc){const r=await pool.query('select room,kind,id,data,deleted,ver from public.items where room=$1 and kind=$2 and id=$3',[row.room,row.kind,row.id]);row=r.rows[0]}
  for(const s of subs){if(s.room!==row.room)continue;
    try{const ok=await asUser(s.uid,c=>c.query('select public.is_member($1) as m',[row.room]));if(ok.rows[0].m)send(s,{t:'pg',row})}catch{}}});
const body=req=>new Promise(r=>{let b='';req.on('data',d=>b+=d);req.on('end',()=>r(b?JSON.parse(b):{}))});
const PRM={join_room:['p_room'],seed_room:['p_room'],apply_ops:['p_room','p_ops'],save_room:['p_room','p_title'],my_rooms:[]};
http.createServer(async(req,res)=>{
  res.setHeader('Access-Control-Allow-Origin','*');res.setHeader('Access-Control-Allow-Headers','*');res.setHeader('Access-Control-Allow-Methods','*');
  if(req.method=='OPTIONS'){res.writeHead(204);return res.end()}
  const u=new URL(req.url,'http://x'),J=(o,c=200)=>{res.writeHead(c,{'content-type':'application/json'});res.end(JSON.stringify(o))};
  try{
  if(u.pathname=='/auth'){const b=await body(req);if(b.op=='signup'){if(pws.has(b.email))return J({error:{message:'User already registered'}});let id=mail.get(b.email)||randomUUID();mail.set(b.email,id);pws.set(b.email,b.password);if(cfg.confirm)return J({pending:true});who.set(id,b.email);return J({uid:id,email:b.email})}
    if(b.op=='signin'){if(!pws.has(b.email)||pws.get(b.email)!==b.password)return J({error:{message:'Invalid login credentials'}});const id=mail.get(b.email);who.set(id,b.email);return J({uid:id,email:b.email})}
    if(b.email){let id=mail.get(b.email);if(!id)mail.set(b.email,id=randomUUID());who.set(id,b.email);return J({uid:id,email:b.email})}return J({uid:randomUUID()})}   // email 이 있으면 같은 이메일=같은 사용자(로그인 흉내)
  if(u.pathname.startsWith('/rpc/')){const fn=u.pathname.slice(5),a=await body(req),uid=req.headers['x-uid'];if(!PRM[fn])return J({error:{message:'Could not find the function '+fn,code:'PGRST202'}},404);
    try{const r=await asUser(uid,c=>c.query(`select public.${fn}(${PRM[fn].map((p,i)=>p+' => $'+(i+1)+(p=='p_ops'?'::jsonb':'')).join(',')}) as r`,PRM[fn].map(p=>p=='p_ops'?JSON.stringify(a[p]):a[p])));return J({data:r.rows[0].r})}
    catch(e){return J({error:{message:e.message,code:e.code}},400)}}
  if(u.pathname=='/items'){const uid=req.headers['x-uid'],room=u.searchParams.get('room'),from=+u.searchParams.get('from'),to=+u.searchParams.get('to'),gt=+(u.searchParams.get('gt')||-1),light=u.searchParams.get('light')=='1',ids=u.searchParams.get('ids')?u.searchParams.get('ids').split(','):null;
    try{const r=await asUser(uid,c=>c.query(`select kind,id,${light?'':'data,'}deleted,ver from public.items where room=$1 and ver>$4 and ($5::text[] is null or id=any($5)) order by ver offset $2 limit $3`,[room,from,to-from+1,gt,ids]));return J({data:r.rows})}catch(e){return J({error:{message:e.message}},400)}}
  if(u.pathname=='/dump'){const r=await pool.query('select kind,id,data,deleted,ver from public.items where room=$1 order by kind,id',[u.searchParams.get('room')]);return J({data:r.rows})}
  if(u.pathname=='/auth/v1/user'){const t=(req.headers.authorization||'').replace(/^Bearer /,'');return t.startsWith('fk_')&&req.headers.apikey?J({id:t.slice(3)}):J({error:'bad token'},401)}   // 사진 Worker 가 부르는 로그인 확인(진짜 Supabase 의 /auth/v1/user 흉내)
  if(u.pathname=='/rtkill'){for(const st of RT.values())for(const w of st)w.terminate();return J({ok:1})}   // 실시간 중계 연결을 서버 쪽에서 전부 끊음
  if(u.pathname=='/rtstat')return J({sockets:[...RT.values()].reduce((n,st)=>n+st.size,0)});
  if(u.pathname=='/r2stat')return J({count:R2.size,keys:[...R2.keys()]});
  if(u.pathname=='/ctl'){Object.assign(cfg,await body(req));return J(cfg)}
  if(u.pathname=='/events'){const sub={res,uid:u.searchParams.get('uid'),room:u.searchParams.get('room'),key:u.searchParams.get('key'),chain:Promise.resolve()};
    res.writeHead(200,{'content-type':'text/event-stream','cache-control':'no-cache',connection:'keep-alive'});res.write(': ok\n\n');subs.add(sub);req.on('close',()=>subs.delete(sub));
    const st=presence.get(sub.room);if(st)send(sub,{t:'presence',state:Object.fromEntries(st)});send(sub,{t:'ready'});return}
  if(u.pathname=='/bcast'){const b=await body(req);for(const s of subs)if(s.room==b.room&&s.key!=b.key)send(s,{t:'bc',event:b.event,payload:b.payload});return J({ok:1})}
  if(u.pathname=='/presence'){const b=await body(req);let st=presence.get(b.room);if(!st)presence.set(b.room,st=new Map());if(b.payload)st.set(b.key,b.payload);else st.delete(b.key);
    for(const s of subs)if(s.room==b.room)send(s,{t:'presence',state:Object.fromEntries(st)});return J({ok:1})}
  }catch(e){return J({error:{message:String(e)}},500)}
  res.writeHead(404);res.end()}).listen(8790,()=>console.log('fake supabase on 8790'));
// 사진 Worker(../worker/photos.mjs)를 진짜 코드 그대로 8791 포트에 올리고, R2 는 메모리로 흉내
const R2=new Map(),r2={async get(k){const v=R2.get(k);return v?{body:v}:null},async head(k){return R2.has(k)?{}:null},async put(k,b){R2.set(k,Buffer.from(b))}};
http.createServer(async(req,res)=>{const ch=[];for await(const c of req)ch.push(c);
  const r=await photoWorker.fetch(new Request('http://localhost:8791'+req.url,{method:req.method,headers:req.headers,body:['GET','HEAD'].includes(req.method)?undefined:Buffer.concat(ch)}),{R2:r2,SB_URL:'http://localhost:8790',SB_KEY:'sb_publishable_test'});
  res.writeHead(r.status,Object.fromEntries(r.headers));res.end(Buffer.from(await r.arrayBuffer()))}).listen(8791,()=>console.log('fake photo worker on 8791'));
// 실시간 중계(../worker/relay.mjs, 진짜 코드)를 8792 포트에 올림 — Cloudflare Durable Object 대신 ws 패키지로 흉내. cfg.mute 면 모든 글을 무시(응답 없는 죽은 연결 흉내)
const RT=new Map(),wss=new WebSocketServer({port:8792});
wss.on('connection',(ws,req)=>{const u=new URL(req.url,'http://x'),m=u.pathname.match(/^\/room\/([\w-]{8,64})$/),k=u.searchParams.get('k')||'';
  if(!m||!/^[\w-]{1,64}$/.test(k))return ws.close(1008);
  const st=RT.get(m[1])||RT.set(m[1],new Set()).get(m[1]);ws.att={k};st.add(ws);
  const peer=x=>({id:x,send:t=>{if(x.readyState==1)x.send(t)},close:c=>x.close(c),get:()=>x.att,set:v=>{x.att=v}}),peers=()=>[...st].map(peer);
  ws.on('message',d=>{if(cfg.mute)return;onMessage(peers(),peer(ws),d.toString(),t=>Promise.resolve(t.startsWith('fk_')))});
  ws.on('close',()=>{st.delete(ws);onLeave(peers(),peer(ws))})});
console.log('fake realtime relay on 8792');
