import json, time, urllib.request
from playwright.sync_api import sync_playwright
import os, tempfile
HERE=os.path.dirname(os.path.abspath(__file__))
STUBS=os.path.join(HERE,'..','stubs')
ROOT=os.path.abspath(os.path.join(HERE,'..','..'))
STUB=open(os.path.join(STUBS,'client_stub.js'),encoding='utf-8').read()
URL='http://localhost:8765/index.html?mode=edit'; API='http://localhost:8790'
def api(path,data=None):
    req=urllib.request.Request(API+path,data=json.dumps(data).encode() if data is not None else None,headers={'content-type':'application/json'},method='POST' if data is not None else 'GET')
    return json.loads(urllib.request.urlopen(req).read())
def canon(x): return json.dumps(x,sort_keys=True,ensure_ascii=False)
def local(pg): return json.loads(pg.evaluate("JSON.stringify({n:S.nodes.map(o=>[o.id,plain(o)]).sort(),l:S.links.map(o=>[o.id,plain(o)]).sort()})"))
def strip(d): d=dict(d);d.pop('id',None);return d
def dbstate(room,pg=None):
    rows=[r for r in api('/dump?room='+room)['data'] if not r['deleted']]
    if pg is not None:
        cl=pg.evaluate("rows=>rows.map(r=>[r.kind,r.id,cleanEnt(r.kind,r.data)])",rows)
        rows=[{'kind':k,'id':i,'data':d} for k,i,d in cl if d is not None]
    n=sorted([[r['id'],r['data']] for r in rows if r['kind']=='n']); l=sorted([[r['id'],r['data']] for r in rows if r['kind']=='l'])
    return {'n':n,'l':l}
def norm(st): return {'n':sorted([[i,strip(d)] for i,d in st['n']]),'l':sorted([[i,strip(d)] for i,d in st['l']])}
def same(*pgs,room):
    st=[norm(local(p)) for p in pgs]+[norm(dbstate(room,pgs[0]))]
    return all(canon(s)==canon(st[0]) for s in st)
def settle(pg,ms=1500): pg.wait_for_timeout(ms)
def client(b,pre=''):
    ctx=b.new_context(viewport={'width':1280,'height':760})
    ctx.route('**/@supabase/supabase-js@2.118.0/+esm',lambda r:r.fulfill(status=200,content_type='application/javascript',body=STUB))
    ctx.add_init_script("try{localStorage.setItem('relmap_sburl','http://localhost:8790');localStorage.setItem('relmap_sbkey','sb_publishable_test')}catch(e){}"+pre)
    pg=ctx.new_page(); pg.on('pageerror',lambda e:ERR.append(str(e))); pg.on('dialog',lambda d:(ERR.append('DIALOG:'+d.message),d.accept())); return pg

ERR=[]   # 테스트 중 발생한 페이지 오류·예상 못한 대화상자가 쌓이는 목록 (모든 테스트가 공유)
ok=lambda n,v:print(('PASS ' if v else 'FAIL ')+n)
