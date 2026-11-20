from helpers import *
# 텍스트 크기(제한 없음·숫자 칸), 읽기 모드 '보는 시점' 선택(이전 사진·설명 보기), 육각형 스탯 기본 6항목 설정
BASE='http://localhost:8765/index.html'
EDIT=BASE+'?mode=edit'
P0='data:image/png;base64,AAAA0';P1='data:image/png;base64,AAAA1';P2='data:image/png;base64,AAAA2';P3='data:image/png;base64,AAAA3'
def mk(b):
    pg=b.new_context(viewport={'width':1280,'height':760}).new_page();pg.on('pageerror',lambda e:ERR.append(str(e)));pg.on('dialog',lambda d:(ERR.append('DIALOG:'+d.message),d.accept()));return pg
SETUP="""(P)=>{S.nodes.push({id:'m1',t:'w',x:0,y:0,title:'영화1',kind:'m',ord:1},{id:'s1',t:'w',x:0,y:0,title:'드라마1',kind:'s',n:3,ord:2},{id:'m9',t:'w',x:0,y:0,title:'안본작품',kind:'m',ord:3});
 const b=nd('b');b.img=P[0];b.im=[{img:P[1],g:'m1'},{img:P[2],g:'s1_2'},{img:P[3],g:'m9'}];b.dx=[{t:'설명영화',g:'m1'},{t:'설명둘째',g:'s1_2'},{t:'설명비공개',g:'m9'},{t:'항상',g:''}];
 const T={id:'T1',t:'t',x:-300,y:300,text:'글자',size:22,bold:false,col:''};S.nodes.push(T);mk(T);upd(T);
 WS.clear();WS.add('m1');WS.add('s1_2');wsSave();sv();drawLinks()}"""
size=lambda pg:pg.evaluate("nd('T1').size")
DEF=['힘','지능','매력','민첩','체력','의지']
with sync_playwright() as p:
    b=p.chromium.launch();pg=mk(b)
    pg.goto(EDIT);settle(pg,700);pg.evaluate(SETUP,[P0,P1,P2,P3]);settle(pg,200)
    # ── 1. 텍스트 크기
    pg.evaluate("select('T1')");settle(pg,150)
    rg=pg.locator('#ins input[type=range][data-k=size]');nb=pg.locator('#ins input[type=number][data-k=size]')
    ok('T1 텍스트 패널에 슬라이더와 숫자 칸이 함께 있고 숫자 칸에 현재 크기가 보임',rg.count()==1 and nb.count()==1 and nb.input_value()=='22')
    nb.fill('500');settle(pg,100)
    ok('T2 숫자 칸에 슬라이더 범위(160)를 넘는 값을 써도 그대로 적용됨',size(pg)==500 and pg.evaluate("els.T1.style.fontSize")=='500px')
    pg.evaluate("(()=>{const r=document.querySelector('#ins input[type=range][data-k=size]');r.value=80;r.dispatchEvent(new Event('input',{bubbles:true}))})()");settle(pg,100)
    ok('T3 슬라이더를 움직이면 크기가 바뀌고 숫자 칸도 따라 바뀜',size(pg)==80 and nb.input_value()=='80')
    for v in ('','0','-5'):nb.fill(v);settle(pg,60)
    nb.fill('999999999');settle(pg,100)
    ok('T4 비었거나 0 이하인 값은 무시하고, 너무 큰 값은 상한(100000)으로 맞춤',size(pg)==100000)
    r=pg.evaluate("cleanDoc({nodes:[{id:'a',t:'t',size:5000},{id:'b',t:'t',size:-5},{id:'c',t:'t',size:'abc'},{id:'d',t:'t',size:1e9}],links:[]}).nodes.map(n=>n.size)")
    ok('T5 불러온 파일의 글자 크기: 큰 값은 허용(상한 100000), 0 이하·이상한 값은 걸러냄',r==[5000,1,22,100000])
    # ── 2. 보는 시점 선택
    pg.evaluate("select(null)");pg.click('#bm');settle(pg,300);pg.evaluate("pfOpen('b')");settle(pg,300)
    sel=pg.locator('#pf [data-ps]');txt=lambda:pg.inner_text('#pf')
    ok('G1 읽기 모드 프로필: 사진·설명이 시청에 따라 바뀌는 인물에 "보는 시점" 선택이 뜨고, 기본은 지금까지 본 것 전부(최신)',sel.count()==1 and [o for o in sel.locator('option').all_inner_texts()]==['지금까지 본 것 전부','처음 모습','영화1까지','드라마1 2화까지'] and pg.evaluate("pimg(nd('b'))")==P2 and '설명영화' in txt() and '설명둘째' in txt() and '항상' in txt())
    sel.select_option(label='영화1까지');settle(pg,200)
    ok('G2 이전 시점(영화1까지)을 고르면 그 시점의 사진·설명만 보이고 캔버스 아이콘도 따라 바뀜',pg.evaluate("pimg(nd('b'))")==P1 and pg.evaluate("els.b._pi")==P1 and '설명영화' in txt() and '설명둘째' not in txt() and '항상' in txt())
    sel.select_option(label='처음 모습');settle(pg,200)
    ok('G3 처음 모습을 고르면 기본 사진과 항상 보이는 설명만 보임',pg.evaluate("pimg(nd('b'))")==P0 and '설명영화' not in txt() and '설명둘째' not in txt() and '항상' in txt())
    sel.select_option(label='지금까지 본 것 전부');settle(pg,200)
    ok('G4 다시 최신으로 돌리면 가장 최근 사진·설명 전부',pg.evaluate("pimg(nd('b'))")==P2 and '설명둘째' in txt())
    ok('G5 안 본 작품(안본작품)의 이름·사진·설명은 선택 목록과 화면에 안 새어 나옴','안본작품' not in sel.inner_text() and '설명비공개' not in txt())
    sel.select_option(label='영화1까지');settle(pg,200);pg.keyboard.press('Escape');settle(pg,150)
    pg.goto(BASE);settle(pg,800);pg.evaluate("pfOpen('b')");settle(pg,300)
    ok('G6 고른 시점은 새로고침해도 유지됨(이 브라우저에만 저장)',pg.input_value('#pf [data-ps]')=='m1' and pg.evaluate("pimg(nd('b'))")==P1)
    pg.keyboard.press('Escape');settle(pg,150);pg.evaluate("pfOpen('c')");settle(pg,250)
    ok('G7 사진·설명이 안 바뀌는 인물에는 선택이 안 뜸',pg.locator('#pf [data-ps]').count()==0)
    pg.keyboard.press('Escape');pg.click('#bm');settle(pg,300)
    # ── 3. 육각형 스탯 기본 항목
    pg.evaluate("select('c')");settle(pg,200)
    closed=pg.locator('#ins [data-sd]').count()==0;pg.click('#ins [data-a=sdo]');settle(pg,150)
    ok('H1 스탯 항목의 기본 설정은 처음엔 접혀 있고 열면 6칸에 기본 항목이 보임(설정 전엔 서버·파일에 아무것도 없음)',closed and [pg.input_value(f'#ins [data-sd="{i}"]') for i in range(6)]==DEF and pg.evaluate("wK('h').length")==0)
    NEW=['공격','방어','속도','지력','운','매우긴이름입니다']
    for i,v in enumerate(NEW):pg.fill(f'#ins [data-sd="{i}"]',v)
    settle(pg,150);pg.click('#ins [data-a=sta]');settle(pg,200)
    ok('H2 바꾼 기본 항목이 저장되고(6글자까지), 새로 만드는 스탯에 그대로 쓰임',pg.evaluate("wK('h')[0].names")==['공격','방어','속도','지력','운','매우긴이름입'] and pg.evaluate("nd('c').st.map(x=>x.n)")==['공격','방어','속도','지력','운','매우긴이름입'] and pg.evaluate("nd('c').st.every(x=>x.v==5)"))
    pg.fill('#ins [data-sd="0"]','변경');settle(pg,150)
    ok('H3 기본 항목을 다시 바꿔도 이미 만든 스탯은 그대로',pg.evaluate("nd('c').st[0].n")=='공격' and pg.evaluate("wK('h').length")==1)
    pg.evaluate("select('d')");settle(pg,200);pg.click('#ins [data-a=sta]');settle(pg,150)
    ok('H4 다른 인물에 새로 만든 스탯은 바꾼 기본 항목으로 시작',pg.evaluate("nd('d').st[0].n")=='변경')
    pg.evaluate("select('b')");settle(pg,200);pg.click('#ins [data-a=sdr]');settle(pg,150);pg.click('#ins [data-a=sta]');settle(pg,150)
    ok('H5 "처음 값으로" 를 누르면 기본 항목이 힘·지능·매력·민첩·체력·의지로 돌아감',pg.evaluate("wK('h').length")==0 and pg.evaluate("nd('b').st.map(x=>x.n)")==DEF)
    r=pg.evaluate("""()=>{const d=cleanDoc({nodes:[{id:'h1',t:'w',kind:'h',names:['a','b'],imp:2,cat:['x']},{id:'h2',t:'w',kind:'h',names:['1234567','b','c','d','e','f'],imp:2,emo:'x',cat:['x']}],links:[]}).nodes;return [d[0].names,d[1].names,d[1].imp,d[1].emo,d[1].cat,d[0].kind]}""")
    ok('H6 불러온 파일의 기본 항목: 6개가 아니면 기본값, 6글자 넘는 이름은 자르고, 다른 작품 필드는 안 붙음',r==[DEF,['123456','b','c','d','e','f'],None,None,None,'h'] and pg.evaluate("[WK().length,PR().length]")==[3,0])
    # ── 4. n각형: 항목 수(3~12)를 사용자가 정함
    pg.evaluate("nd('b').st[0].v=9;select(null);select('b')");settle(pg,200)
    nb=pg.locator('#ins [data-nn]');pts=lambda s:pg.eval_on_selector(s,"e=>e.getAttribute('points').trim().split(' ').length");stn=lambda:pg.evaluate("nd('b').st.length")
    def setn(v):
        nb.fill(v);nb.press('Tab');settle(pg,200)
    f0=nb.input_value();setn('8')
    ok('N1 스탯 패널에 항목 수 칸(처음 6)이 있고 8로 바꾸면 8각형이 됨(새 항목은 이름·값 5, 기존 항목은 그대로)',f0=='6' and stn()==8 and pg.evaluate("nd('b').st.slice(6).map(x=>x.n+x.v)")==['항목75','항목85'] and pg.evaluate("nd('b').st[0].v")==9 and pg.evaluate("nd('b').st.slice(0,6).map(x=>x.n)")==DEF and pts('#hxp svg polygon[fill]')==8 and pg.locator('#hxp svg polygon.hg').count()==5 and '8각형 스탯' in pg.inner_text('#ins'))
    setn('3')
    ok('N2 3으로 줄이면 뒤 항목이 빠지고 삼각형이 됨',stn()==3 and pg.evaluate("nd('b').st.map(x=>x.n)")==DEF[:3] and pts('#hxp svg polygon[fill]')==3 and '3각형 스탯' in pg.inner_text('#ins'))
    setn('2');a=stn();setn('13');c=stn();setn('');d=stn()
    ok('N3 항목 수: 3 미만·빈 값은 무시하고 12 를 넘으면 12 로 맞춤',[a,c,d]==[3,12,12] and nb.input_value()=='12')
    pg.click('#bm');settle(pg,300);pg.evaluate("pfOpen('b')");settle(pg,300)
    ok('N4 읽기 모드 프로필 모달에도 12각형(꼭짓점·이름 12개)이 그려짐',pg.eval_on_selector('#pf svg.hx polygon[fill]',"e=>e.getAttribute('points').trim().split(' ').length")==12 and pg.locator('#pf svg.hx text.ht').count()==12)
    pg.keyboard.press('Escape');pg.click('#bm');settle(pg,300)
    pg.evaluate("S.nodes.push({id:'p9',t:'p',x:300,y:-200,name:'새',desc:'',img:'',col:'#0066FF'});mk(nd('p9'));select('p9')");settle(pg,200)
    sn=pg.locator('#ins [data-sdn]');dn=lambda:pg.evaluate("sNames()")
    sn.fill('4');sn.press('Tab');settle(pg,200);k1=[sn.input_value(),pg.locator('#ins [data-sd]').count(),dn()]
    pg.click('#ins [data-a=sta]');settle(pg,200);k2=pg.evaluate("nd('p9').st.map(x=>x.n)")
    sn.fill('8');sn.press('Tab');settle(pg,200)
    ok('N5 기본 항목 수를 4로 바꾸면 4칸·새 스탯도 4항목이고, 8로 늘리면 모자란 칸은 기본 이름/"항목N" 으로 채워지며 이미 만든 스탯은 그대로',k1==['4',4,DEF[:4]] and k2==DEF[:4] and dn()==DEF+['항목7','항목8'] and pg.evaluate("nd('p9').st.length")==4)
    r=pg.evaluate("""()=>{const mkp=n=>({id:'p'+n,t:'p',x:0,y:0,name:'a',st:Array.from({length:n},(_,i)=>({n:'i'+i,v:5}))}),mkh=(id,n)=>({id,t:'w',kind:'h',names:Array.from({length:n},(_,i)=>'n'+i)});
      const d=cleanDoc({nodes:[mkp(2),mkp(3),mkp(12),mkp(13),mkh('h2',2),mkh('h3',3),mkh('h12',12),mkh('h13',13)],links:[]}).nodes;return [d.slice(0,4).map(n=>n.st?n.st.length:0),d.slice(4).map(n=>n.names.length)]}""")
    ok('N6 불러온 파일의 항목 수: 스탯·기본 항목은 3~12개만 인정(그 밖은 스탯 없음/기본 6항목)',r==[[0,3,12,0],[6,3,12,6]])
    # ── 방 안: 기본 항목·큰 글자 크기가 동기화됨
    A=client(b,"");B=client(b,"")
    A.goto(EDIT);settle(A,500);A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    B.goto(BASE+h);settle(B,1800)
    A.evaluate("(()=>{const T={id:'T9',t:'t',x:-300,y:300,text:'글자',size:22,bold:false,col:''};S.nodes.push(T);mk(T);upd(T);sv();select('c')})()");settle(A,200)
    A.click('#ins [data-a=sdo]');A.fill('#ins [data-sd="0"]','방공격');A.evaluate("select('T9')");settle(A,150);A.locator('#ins input[type=number][data-k=size]').fill('700');settle(A,300)
    A.evaluate("select('b')");settle(A,200);A.click('#ins [data-a=sta]');settle(A,150);A.locator('#ins [data-nn]').fill('9');A.locator('#ins [data-nn]').press('Tab');settle(A,1800)
    ok('R1 방: 기본 항목 설정·700 같은 큰 글자 크기·9각형 스탯이 B·DB 에 똑같이 반영됨',same(A,B,room=room) and B.evaluate("[wK('h')[0].names[0],nd('T9').size,nd('b').st.length]")==['방공격',700,9])
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    b.close()
