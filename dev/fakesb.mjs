// Supabase 흉내 서버: 진짜 SQL 함수(Postgres)를 그대로 쓰고, PostgREST/Realtime 의 겉모습만 흉내냄
import http from 'http'; import pg from 'pg'; import {randomUUID} from 'crypto';
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
  if(u.pathname=='/items'){const uid=req.headers['x-uid'],room=u.searchParams.get('room'),from=+u.searchParams.get('from'),to=+u.searchParams.get('to');
    try{const r=await asUser(uid,c=>c.query('select kind,id,data,deleted,ver from public.items where room=$1 order by ver offset $2 limit $3',[room,from,to-from+1]));return J({data:r.rows})}catch(e){return J({error:{message:e.message}},400)}}
  if(u.pathname=='/dump'){const r=await pool.query('select kind,id,data,deleted,ver from public.items where room=$1 order by kind,id',[u.searchParams.get('room')]);return J({data:r.rows})}
  if(u.pathname=='/ctl'){Object.assign(cfg,await body(req));return J(cfg)}
  if(u.pathname=='/events'){const sub={res,uid:u.searchParams.get('uid'),room:u.searchParams.get('room'),key:u.searchParams.get('key'),chain:Promise.resolve()};
    res.writeHead(200,{'content-type':'text/event-stream','cache-control':'no-cache',connection:'keep-alive'});res.write(': ok\n\n');subs.add(sub);req.on('close',()=>subs.delete(sub));
    const st=presence.get(sub.room);if(st)send(sub,{t:'presence',state:Object.fromEntries(st)});send(sub,{t:'ready'});return}
  if(u.pathname=='/bcast'){const b=await body(req);for(const s of subs)if(s.room==b.room&&s.key!=b.key)send(s,{t:'bc',event:b.event,payload:b.payload});return J({ok:1})}
  if(u.pathname=='/presence'){const b=await body(req);let st=presence.get(b.room);if(!st)presence.set(b.room,st=new Map());if(b.payload)st.set(b.key,b.payload);else st.delete(b.key);
    for(const s of subs)if(s.room==b.room)send(s,{t:'presence',state:Object.fromEntries(st)});return J({ok:1})}
  }catch(e){return J({error:{message:String(e)}},500)}
  res.writeHead(404);res.end()}).listen(8790,()=>console.log('fake supabase on 8790'));
