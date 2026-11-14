import json, os, re, urllib.request, tempfile
from playwright.sync_api import sync_playwright
from helpers import *
ok=lambda n,v:print(('PASS ' if v else 'FAIL ')+n)
def rpc(uid,fn,args):
    req=urllib.request.Request(API+'/rpc/'+fn,data=json.dumps(args).encode(),headers={'content-type':'application/json','x-uid':uid},method='POST')
    try: return json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as e: return json.loads(e.read())
def solo(b):
    ctx=b.new_context(viewport={'width':1280,'height':760},accept_downloads=True);pg=ctx.new_page();pg.dialogs=[];pg.on('pageerror',lambda e:ERR.append(str(e)));pg.on('dialog',lambda d,pg=pg:(pg.dialogs.append(d.message),d.accept()));return pg
def do_import(pg,path):
    with pg.expect_file_chooser() as fc: pg.click('#bl')
    fc.value.set_files(path);pg.wait_for_timeout(900)
def export(pg):
    with pg.expect_download() as d: pg.click('#bs')
    path=tempfile.mktemp(suffix='.json');d.value.save_as(path);return d.value.suggested_filename,path
def nopos(st):
    f=lambda d:{**{k:v for k,v in d.items() if k not in('x','y','h','base')},**({'o':d.get('o',30),'w':d.get('w',5)} if 'a' in d else {})}
    return {'n':sorted([[i,f(d)] for i,d in st['n']]),'l':sorted([[i,f(d)] for i,d in st['l']])}
docnorm=lambda pg:nopos(norm(local(pg)))
with sync_playwright() as p:
    b=p.chromium.launch()
    # ── 혼자 쓸 때: 저장/불러오기
    A=solo(b);A.goto(URL);A.wait_for_timeout(700);A.evaluate('alpha=0')
    ok('J0 저장 버튼이 항상 보임',A.eval_on_selector('#bs','e=>getComputedStyle(e).display!="none"'))
    fn,path=export(A);doc=json.load(open(path,encoding='utf-8'))
    ok('J1 JSON 저장(파일명·구조·임시값 제외)',re.fullmatch(r'인물관계도_\d{4}-\d{2}-\d{2}\.json',fn) is not None and doc['app']=='relmap' and len(doc['nodes'])==5 and len(doc['links'])==2 and 'view' not in doc and 'vx' not in json.dumps(doc) and '"_' not in json.dumps(doc))
    B=solo(b);B.goto(URL);B.wait_for_timeout(600);B.evaluate("S.nodes=[];S.links=[];W.querySelectorAll('.n,.lb').forEach(x=>x.remove());els={};lels={};sv()");do_import(B,path)
    ok('J2 저장한 파일을 다시 불러오면 같은 관계도',canon(docnorm(B))==canon(docnorm(A)) and B.inner_text('#bl .bt') in('불러옴','불러오기') and all(abs(a[1]['x']-b_[1]['x'])<60 for a,b_ in zip(sorted(norm(local(A))['n']),sorted(norm(local(B))['n'])) if 'x' in a[1] and a[1].get('t')=='p'))
    bad=tempfile.mktemp(suffix='.json');open(bad,'w').write('{"nodes":"x"}');before=canon(docnorm(B));do_import(B,bad)
    bad2=tempfile.mktemp(suffix='.json');open(bad2,'w').write('이건 JSON 이 아님');do_import(B,bad2)
    ok('J3 잘못된 파일은 거부되고 기존 관계도는 그대로',canon(docnorm(B))==before)
    # 더러운 파일: 긴/이상한/중복 id, 스크립트 주입 값, 존재하지 않는 참조
    dirty={'nodes':[
      {'id':'x'*90,'t':'p','x':0,'y':0,'name':'긴아이디','col':'#0066FF','img':''},
      {'id':'dup','t':'p','x':100,'y':0,'name':'첫번째','col':'#0066FF','img':''},
      {'id':'dup','t':'p','x':200,'y':0,'name':'두번째(중복id)','col':'#0066FF','img':''},
      {'id':'__proto__','t':'p','x':0,'y':100,'name':'proto','col':'#0066FF','img':''},
      {'id':'a"b','t':'p','x':50,'y':100,'name':'따옴표id','col':'#0066FF','img':''},
      {'id':'inj','t':'p','x':300,'y':100,'name':'<img src=x onerror=window.__pwned=1>','img':'http://evil.example/t.png','col':'#12345" onmouseover="window.__pwned=1'},
      {'id':'huge','t':'p','x':1e300,'y':'NaN','name':'큰값','col':'#0066FF','img':'javascript:alert(1)'},
      {'id':'grp','t':'c','x':0,'y':0,'w':'abc','h':-5,'title':'그룹','col':'#6541F2','m':['dup','없는사람','x'*90,{'a':1}]},
      {'id':'weird','t':'zzz'}],
     'links':[
      {'id':'l1','a':'dup','b':'inj','label':'정상선','col':'red" onmouseover="window.__pwned=1" x="','w':'5" onmouseover="window.__pwned=1','o':30},
      {'id':'l2','a':'dup','b':'없는사람','label':'끊긴선','col':'#70737C','w':5,'o':30},
      {'id':'l1','a':'inj','b':'dup','label':'중복id선','col':'#70737C','w':5,'o':30},
      {'id':'l"3','a':'x'*90,'b':'dup','label':'긴id참조','col':'#70737C','w':5,'o':30}]}
    dp=tempfile.mktemp(suffix='.json');json.dump(dirty,open(dp,'w'));C=solo(b);C.goto(URL);C.wait_for_timeout(600);C.evaluate('alpha=0');do_import(C,dp)
    st=C.evaluate("({n:S.nodes.map(n=>n.id),l:S.links.map(l=>[l.id,l.a,l.b,l.col,l.w]),imgs:S.nodes.map(n=>n.img).filter(Boolean),xs:S.nodes.map(n=>n.x)})")
    C.evaluate("document.querySelectorAll('#ln line,.lb,.n').forEach(e=>{e.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));e.dispatchEvent(new PointerEvent('pointerover',{bubbles:true}))})");C.wait_for_timeout(300)
    ok('J4a 이상한 id 는 새 id 로 바뀌거나 제외됨(모두 안전한 형식)',all(re.fullmatch(r'[A-Za-z0-9_-]{1,64}',i) for i in st['n']) and '__proto__' not in st['n'] and len(set(st['n']))==len(st['n']))
    ok('J4b 중복 id 인물도 둘 다 살아남고, 알 수 없는 종류는 제외',C.evaluate("S.nodes.filter(n=>n.name&&(n.name.startsWith('두번째')||n.name=='첫번째')).length")==2 and C.evaluate("S.nodes.every(n=>['p','t','c'].includes(n.t))"))
    ok('J4c 존재하지 않는 인물을 가리키는 선은 제외, 나머지 선은 정상 id',len(st['l'])>=1 and all(re.fullmatch(r'[A-Za-z0-9_-]{1,64}',l[0]) for l in st['l']) and all(l[3]=='#70737C' or re.fullmatch(r'#[0-9a-fA-F]{6}',l[3]) for l in st['l']))
    ok('J4d 외부 주소·javascript 그림 제거, 비정상 숫자는 범위로 보정',st['imgs']==[] and all(abs(x)<=1e6 for x in st['xs']))
    ok('J4e 스크립트 주입 시도가 실행되지 않음(호버 포함)·이벤트 속성 없음',C.evaluate('window.__pwned')is None and C.evaluate("document.querySelectorAll('#ln *,#ins *,.n *,.lb').length>0&&![...document.querySelectorAll('#ln *,#ins *,.n,.n *,.lb')].some(e=>[...e.attributes].some(a=>a.name.startsWith('on')))"))
    n0=C.evaluate('S.nodes.length');C.click('button[data-t="p"]');C.wait_for_timeout(400)
    ok('J4f 불러온 뒤에도 앱이 정상 동작',C.evaluate('S.nodes.length')==n0+1)
    # ── 공동 편집 중
    Ar=client(b);Br=client(b);Ar.on('dialog',lambda d:None)
    Ar.goto(URL);settle(Ar,500);Ar.click('#bk');settle(Ar,1500);h=Ar.evaluate('location.hash');room=h.split('room=')[1]
    Br.goto(URL+h);settle(Br,1800)
    ok('J5a 공동 편집 중에도 저장/불러오기 버튼 사용 가능, 초기화만 막힘',Ar.eval_on_selector('#bs','e=>!e.disabled')and Ar.eval_on_selector('#bl','e=>!e.disabled')and Ar.eval_on_selector('#br','e=>e.disabled'))
    fn2,path2=export(Ar);saved=json.load(open(path2,encoding='utf-8'))
    # A가 문서를 바꿈(인물 삭제+이름 변경) → 그 뒤 저장본을 불러옴
    Ar.click('.p[data-id="d"] .im');Ar.keyboard.press('Delete');Ar.evaluate("nd('c').name='바꾼 이름';upd(nd('c'));sv()");settle(Ar,1500)
    changed=norm(local(Ar))
    Ar.evaluate("window.__cm=null;window.confirm=m=>{window.__cm=m;return false}")
    do_import(Ar,path2);cm=Ar.evaluate('window.__cm')
    ok('J6 확인창에서 취소하면 아무것도 바뀌지 않음(경고 문구 표시)',same(Ar,Br,room=room) and canon(norm(local(Ar)))==canon(changed) and bool(cm) and '방' in cm)
    Ar.evaluate("window.confirm=m=>true")
    do_import(Ar,path2);settle(Ar,2500)
    orig_norm={'n':sorted([[n['id'],strip({k:v for k,v in n.items() if k not in('vx','vy','fx','fy')})] for n in saved['nodes']]),'l':sorted([[l['id'],strip(l)] for l in saved['links']])}
    ok('J5b 방 안에서 불러오면 B·DB 에도 파일 내용이 반영',same(Ar,Br,room=room) and canon(local_ids:=sorted([n[0] for n in norm(local(Br))['n']]))==canon(sorted([n['id'] for n in saved['nodes']])))
    Ar.click('#bun');settle(Ar,2500)
    ok('J5c 실행 취소 한 번으로 불러오기 전 상태로 복원(A·B·DB)',same(Ar,Br,room=room) and canon(norm(local(Ar)))==canon(changed))
    Ar.click('#bre');settle(Ar,2500)
    ok('J5d 다시 실행하면 불러온 내용으로 복귀',same(Ar,Br,room=room) and sorted([n[0] for n in norm(local(Ar))['n']])==sorted([n['id'] for n in saved['nodes']]))
    # 더러운 파일을 방 안에서 불러와도 서버가 거부하지 않음(id 정리됨)
    Ar.evaluate("window.__fails=0");do_import(Ar,dp);settle(Ar,3500)
    dbids=[r['id'] for r in api('/dump?room='+room)['data'] if not r['deleted']]
    ok('J7 더러운 파일을 방 안에서 불러와도 저장됨(모든 id 안전, 전송 지연 없음)',same(Ar,Br,room=room) and all(re.fullmatch(r'[A-Za-z0-9_-]{1,64}',i) for i in dbids) and Ar.inner_text('#bk .bt')=='링크 복사' and Ar.evaluate('fails')==0)
    # 큰 파일(300명+250선)
    big={'nodes':[{'id':'n%03d'%i,'t':'p','x':(i%20)*120,'y':(i//20)*120,'name':'P%d'%i,'desc':'','img':'','col':'#0066FF'} for i in range(300)],'links':[{'id':'l%03d'%i,'a':'n%03d'%i,'b':'n%03d'%(i+1),'label':'','col':'#70737C','w':5,'o':30} for i in range(250)]}
    bp=tempfile.mktemp(suffix='.json');json.dump(big,open(bp,'w'));do_import(Ar,bp);settle(Ar,9000)
    rows=[r for r in api('/dump?room='+room)['data'] if not r['deleted']]
    ok('J8 큰 파일(300명·250선)도 나눠서 저장되고 B 와 동일 (%d행)'%len(rows),len(rows)==550 and same(Ar,Br,room=room))
    Ar.click('#bun');settle(Ar,20000)
    ok('J8b 큰 불러오기도 실행 취소 한 번으로 복원',same(Ar,Br,room=room) and len(local(Ar)['n'])!=300)
    # ── 악의적 참가자가 서버로 직접 보낸 값
    evil=json.loads(urllib.request.urlopen(urllib.request.Request(API+'/auth',data=b'{}',method='POST')).read())['uid']
    rpc(evil,'join_room',{'p_room':room})
    ops=[{'k':'l','id':'evilL1','put':{'a':'b','b':'c','label':'<img src=x onerror=window.__pwned=1>','col':'red" onmouseover="window.__pwned=1" x="','w':'5" onmouseover="window.__pwned=1','o':30,'dir':'to'}},
         {'k':'n','id':'__proto__','put':{'t':'p','x':1,'y':2,'name':'proto'}},
         {'k':'n','id':'constructor','put':{'t':'p','x':1,'y':2,'name':'ctor'}},
         {'k':'n','id':'x" onmouseover="window.__pwned=1','put':{'t':'p','x':5,'y':5,'name':'inj','img':'http://evil.example/x.png','col':'#12345" onmouseover="window.__pwned=1'}},
         {'k':'n','id':'bigx','put':{'t':'p','x':1e300,'y':'NaN','name':'<script>window.__pwned=1</script>','col':'#0066FF','img':'javascript:alert(1)'}},
         {'k':'n','id':'objname','put':{'t':'p','x':0,'y':0,'name':{'a':1},'desc':[1,2]}},
         {'k':'n','id':'badtype','put':{'t':'z'}}]
    r=rpc(evil,'apply_ops',{'p_room':room,'p_ops':ops});settle(Br,2500)
    Br.evaluate("document.querySelectorAll('#ln line,.lb,.n').forEach(e=>{e.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));e.dispatchEvent(new PointerEvent('pointerover',{bubbles:true}))})")
    Br.evaluate("select('evilL1')");Br.wait_for_timeout(500)
    bs=Br.evaluate("({ids:S.nodes.map(n=>n.id),ev:S.links.find(l=>l.id=='evilL1')})")
    ok('X1 서버로 직접 보낸 악의적 값: 위험한 id(__proto__·따옴표 등)와 알 수 없는 종류는 무시',not any(i in bs['ids'] for i in('__proto__','constructor','badtype')) and not any('onmouseover' in i for i in bs['ids']))
    ok('X2 색·굵기는 안전한 값으로 보정되고 라벨은 글자로만 표시',bs['ev'] and bs['ev']['col']=='#70737C' and bs['ev']['w']==5)
    ok('X3 스크립트가 실행되지 않음(호버·패널 포함)·이벤트 속성 없음',Br.evaluate('window.__pwned')is None and Br.evaluate("![...document.querySelectorAll('#ln *,#ins *,.n,.n *,.lb')].some(e=>[...e.attributes].some(a=>a.name.startsWith('on')))") and Br.evaluate("document.querySelectorAll('img').length")==0)
    ok('X4 이상한 숫자/이름도 안전하게 처리되고 B 는 계속 정상 동작·동기화',Br.evaluate("(()=>{const n=nd('bigx');return n&&Math.abs(n.x)<=1e6&&n.img===''})()") and True)
    pid=Br.evaluate("S.nodes.find(n=>n.t=='p'&&n.id!='bigx'&&n.id!='objname').id")
    Br.evaluate(f"nd('{pid}').desc='정상 편집';upd(nd('{pid}'));sv()");settle(Br,1800)
    ok('X5 악의적 데이터가 있어도 정상 편집이 계속 전달됨',Ar.evaluate(f"nd('{pid}')&&nd('{pid}').desc")=='정상 편집')
    print('errors:',[e for e in ERR if 'JSON' not in e][:5]);b.close()
