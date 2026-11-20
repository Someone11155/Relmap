from helpers import *
# 작품 중요도(굵기·크기·이모지) + 카테고리 프리셋·카테고리(여러 개 지정, 펼쳐 보기), 검증, 방 동기화
BASE='http://localhost:8765/index.html'
EDIT=BASE+'?mode=edit'
vis=lambda pg,s:pg.eval_on_selector(s,'e=>getComputedStyle(e).display')!='none'
def mk(b):
    pg=b.new_context(viewport={'width':1280,'height':760}).new_page();pg.on('pageerror',lambda e:ERR.append(str(e)));pg.on('dialog',lambda d:(ERR.append('DIALOG:'+d.message),d.accept()));return pg
cat=lambda pg,i:pg.evaluate("i=>(nd(i).cat||[]).slice().sort()",i)
def add(pg,kind,name):
    pg.click(f'[data-wa={kind}]');pg.keyboard.type(name);settle(pg,100)
with sync_playwright() as p:
    b=p.chromium.launch();pg=mk(b)
    pg.goto(EDIT);settle(pg,700);pg.click('#bw')
    add(pg,'m','영화A');add(pg,'s','드라마B');add(pg,'m','영화C')
    A,B,C=pg.evaluate("WK().map(w=>w.id)")
    add(pg,'q','장르');add(pg,'k','액션');add(pg,'k','가족')
    pre=pg.evaluate("curP()");c1,c2=pg.evaluate("CK(curP()).map(c=>c.id)")
    ok('C1 프리셋과 카테고리 2개를 만들 수 있고, 만든 프리셋이 선택됨',pg.evaluate("[PR().length,CK(curP()).map(c=>c.title)]")==[1,['액션','가족']] and pg.evaluate("localStorage.getItem(cpKey())")==pre)
    pg.check(f'[data-wc="{A}"][data-cc="{c1}"]');pg.check(f'[data-wc="{B}"][data-cc="{c1}"]');pg.check(f'[data-wc="{B}"][data-cc="{c2}"]')
    ok('C2 카테고리를 펼치면 작품 체크 목록이 보이고, 한 작품을 여러 카테고리에 넣을 수 있음',cat(pg,A)==[c1] and cat(pg,B)==sorted([c1,c2]) and cat(pg,C)==[] and '(2/3)' in pg.inner_text(f'[data-ckx="{c1}"]'))
    pg.fill(f'[data-wo="{B}"]','🔥');pg.select_option(f'[data-wi="{B}"]','2');settle(pg,100)
    pg.click('[data-wa=x]');pg.evaluate("select('b')");settle(pg,150);pg.click('[data-tgd]');settle(pg,100)
    r=pg.evaluate("""(B)=>{const sp=[...document.querySelectorAll('#ins .ddl .wi2')][0],n=[...document.querySelectorAll('#ins .ddl .wi0')][0];return [sp&&sp.textContent.startsWith('🔥'),sp&&+getComputedStyle(sp).fontWeight>=700,sp&&n&&parseFloat(getComputedStyle(sp).fontSize)>parseFloat(getComputedStyle(n).fontSize)]}""",B)
    ok('C3 중요도·이모지: 작품 이름 앞에 이모지가 붙고, 아주 중요한 작품은 더 굵고 크게 보임',pg.evaluate("i=>[nd(i).emo,nd(i).imp]",B)==['🔥',2] and r==[True,True,True])
    r2=pg.evaluate("""()=>{const d=cleanDoc(JSON.parse(JSON.stringify({nodes:S.nodes,links:S.links})));return [d.nodes.filter(n=>n.t=='w').map(n=>[n.kind,n.title,n.imp||0,n.emo||'',(n.cat||[]).length,n.pre||'']).sort()]}""")
    ok('C4 저장·불러오기(JSON) 왕복에서 프리셋·카테고리·중요도·이모지·카테고리 지정이 유지됨',r2==[sorted([['m','영화A',0,'',1,''],['s','드라마B',2,'🔥',2,''],['m','영화C',0,'',0,''],['q','장르',0,'',0,''],['k','액션',0,'',0,pre],['k','가족',0,'',0,pre]])])
    pg.click('#bm');settle(pg,300);pg.click('#bq');settle(pg,200)
    pg.click(f'[data-ckx="{c1}"]');pg.click(f'[data-ckx="{c2}"]');settle(pg,100)   # 방금 만든 카테고리는 펼쳐진 채로 시작하므로 접어서 확인
    t=pg.inner_text('#wk')
    ok('C5 읽기 모드: 프리셋을 고르면 카테고리만 접혀서 보이고(작품은 안 보임), 분류 없는 작품은 미분류로 묶임',pg.input_value('[data-qs]')==pre and pg.locator('#wk [data-ww],#wk [data-wwp]').count()==0 and '액션 (2)' in t and '가족 (1)' in t and '미분류 (1)' in t)
    pg.click(f'[data-ckx="{c1}"]');pg.click(f'[data-ckx="{c2}"]');pg.click('[data-ckx="_none"]');settle(pg,100)
    t=pg.inner_text('#wk')
    ok('C6 카테고리를 펼치면 안의 작품이 보이고, 여러 카테고리에 든 작품은 각각에 보임',pg.locator('#wk [data-ww],#wk [data-wwp]').count()==4 and t.count('🔥 드라마B')==2 and pg.locator('#wk .wi2').count()==2)
    pg.select_option('[data-qs]','');settle(pg,100)
    ok('C7 프리셋 없이 모두 보기를 고르면 작품이 한 줄로 모두 보임',pg.locator('#wk [data-ww],#wk [data-wwp]').count()==3 and not pg.locator('[data-ckx]').count())
    pg.select_option('[data-qs]',pre);pg.click('#bq');pg.click('#bm');settle(pg,300);pg.click('#bw');settle(pg,200)
    pg.click(f'[data-wd="{c2}"]');pg.click(f'[data-wd="{c2}"]');settle(pg,150)
    ok('C8 카테고리를 지우면(두 번 확인) 작품의 카테고리 지정에서도 빠짐',pg.evaluate("CK(curP()).length")==1 and cat(pg,B)==[c1])
    pg.click(f'[data-wd="{pre}"]');pg.click(f'[data-wd="{pre}"]');settle(pg,150)
    ok('C9 프리셋을 지우면 안의 카테고리도 함께 지워지고 선택이 풀림',pg.evaluate("[PR().length,S.nodes.filter(n=>n.kind=='k').length,curP(),WK().every(w=>!(w.cat||[]).length)]")==[0,0,'',True] and pg.evaluate("localStorage.getItem(cpKey())")=='')
    r=pg.evaluate("""()=>{const d=cleanDoc({nodes:[{id:'w1',t:'w',kind:'m',title:'a',imp:9,emo:'😀😀😀😀😀',cat:['ok','bad id','__proto__','ok'],ord:1},{id:'k1',t:'w',kind:'k',title:'k',pre:'bad id',imp:2,ord:2},{id:'q1',t:'w',kind:'q',title:'q',imp:2,emo:'x',cat:['a'],ord:3},{id:'w2',t:'w',kind:'zzz',title:'z',imp:'abc',emo:7,cat:'no',ord:4}],links:[]}).nodes;return [d[0].imp,d[0].emo,d[0].cat,d[1].kind,d[1].pre,d[1].imp,d[2].kind,d[2].imp,d[2].emo,d[2].cat,d[3].kind,d[3].imp,d[3].emo,d[3].cat]}""")
    ok('C10 불러온 파일의 잘못된 중요도·이모지·카테고리·프리셋 값은 걸러짐',r==[2,'😀😀😀',['ok'],'k','',None,'q',None,None,None,'m',None,None,None])
    # ── 방 안: 프리셋·카테고리·지정이 동기화됨
    X=client(b,"");Y=client(b,"")
    X.goto(EDIT);settle(X,500);X.click('#bk');settle(X,1500);h=X.evaluate('location.hash');room=h.split('room=')[1]
    Y.goto(BASE+h);settle(Y,1800)
    X.click('#bw');add(X,'m','방영화');add(X,'q','방프리셋');add(X,'k','방카테고리');settle(X,300)
    w=X.evaluate("WK()[0].id");c=X.evaluate("CK(curP())[0].id");X.check(f'[data-wc="{w}"][data-cc="{c}"]');X.fill(f'[data-wo="{w}"]','⭐');X.select_option(f'[data-wi="{w}"]','1');settle(X,1800)
    ok('R1 방: 프리셋·카테고리·카테고리 지정·중요도·이모지가 B·DB 에 똑같이 반영됨',same(X,Y,room=room) and Y.evaluate("[PR().length,CK(PR()[0].id).length,WK()[0].cat.length,WK()[0].imp,WK()[0].emo]")==[1,1,1,1,'⭐'])
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    b.close()
