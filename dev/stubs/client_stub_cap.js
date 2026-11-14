// 브라우저용 supabase-js 흉내 (실제 클라이언트가 쓰는 부분만)
const BASE='http://localhost:8790';
export function createClient(url,key,opts){
 const L=localStorage,uid=()=>L.getItem('fk_uid');
 const auth={async getSession(){const u=uid();return{data:{session:u?{user:{id:u}}:null}}},
  async signInAnonymously(c){window.__signinArgs=c||null;if(window.__needCaptcha&&!(c&&c.options&&c.options.captchaToken))return{data:null,error:{message:'captcha protection: request disallowed (no captcha_token found)'}};const d=await (await fetch(BASE+'/auth',{method:'POST'})).json();L.setItem('fk_uid',d.uid);return{data:{user:{id:d.uid}},error:null}}};
 const wait=()=>new Promise(r=>setTimeout(r,window.__rpcDelay||0));
 async function rpc(fn,args){await wait();const r=await fetch(BASE+'/rpc/'+fn,{method:'POST',headers:{'content-type':'application/json','x-uid':uid()},body:JSON.stringify(args)});const d=await r.json();window.__rpcCount=(window.__rpcCount||0)+1;return d.error?{data:null,error:d.error}:{data:d.data,error:null}}
 function from(){const q={room:null,a:0,b:999},b={select(){return b},eq(c,v){q.room=v;return b},order(){return b},range(a,z){q.a=a;q.b=z;return b},
  then(res,rej){return fetch(BASE+'/items?room='+q.room+'&from='+q.a+'&to='+q.b,{headers:{'x-uid':uid()}}).then(r=>r.json()).then(d=>d.error?{data:null,error:d.error}:{data:d.data,error:null}).then(res,rej)}};return b}
 function channel(name,cfg){window.__chanCount=(window.__chanCount||0)+1;const room=name.replace('relmap:',''),key=cfg.config.presence.key,h={pg:[],bc:[],pres:[]};let es=null,state={},cbSub=null;
  const open=()=>{es=new EventSource(BASE+'/events?room='+room+'&uid='+uid()+'&key='+key);
   es.onmessage=e=>{const m=JSON.parse(e.data);
    if(m.t=='ready'){ch.state='joined';cbSub&&cbSub('SUBSCRIBED')}
    else if(m.t=='pg')h.pg.forEach(x=>x.cb({eventType:'UPDATE',new:m.row}));
    else if(m.t=='bc')h.bc.filter(x=>x.f.event==m.event).forEach(x=>x.cb({type:'broadcast',event:m.event,payload:m.payload}));
    else if(m.t=='presence'){state=m.state;h.pres.forEach(x=>x.cb())}}};
  const post=(p,b)=>fetch(BASE+p,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(b)});
  const ch={state:'joining',on(t,f,cb){(t=='postgres_changes'?h.pg:t=='broadcast'?h.bc:h.pres).push({f,cb});return ch},
   subscribe(cb){cbSub=cb;ch._cb=cb;open();window.__sbDrop=ms=>{es.close();setTimeout(open,ms)};window.__sbKill=st=>{es&&es.close();ch.state=st=='CLOSED'?'closed':'errored';cbSub(st)};return ch},
   async track(p){await post('/presence',{room,key,payload:p});return'ok'},async untrack(){await post('/presence',{room,key,payload:null});return'ok'},
   async send(a){await post('/bcast',{room,key,event:a.event,payload:a.payload});return'ok'},
   presenceState(){const o={};for(const k in state)o[k]=[state[k]];return o},close(){es&&es.close()}};return ch}
 return{auth,rpc,from,channel,removeChannel(ch){ch.close();ch.state='closed';ch._cb&&ch._cb('CLOSED')}}}
