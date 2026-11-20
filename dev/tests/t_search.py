from helpers import *
# 검색(인물 이름·그룹·작품, 부드러운 이동, 읽기 모드 스포일러, 한글 조합 중 Enter) + 그룹 크기 핸들(확대·축소·좁은 화면)
EDIT='http://localhost:8765/index.html?mode=edit'
SETUP="""()=>{S.nodes=[];S.links=[];W.querySelectorAll('.n,.lb').forEach(x=>x.remove());els={};lels={};
 const P=(id,name,x,y,tg)=>{const n={id,t:'p',x,y,name,desc:'',img:'',col:'#0066FF'};if(tg)n.tg=tg;S.nodes.push(n);mk(n)};
 P('a','김서준',-300,-100,['m1']);P('b','이하린',0,-100,['m1']);P('c','박도윤',300,-100,['s1_2']);P('d','Alice Kim',600,400,['s1_3']);P('e','서연',-300,300);P('f','<img src=x onerror=window.__x=1>',0,300,['m9']);
 S.nodes.push({id:'m1',t:'w',x:0,y:0,title:'영화1',kind:'m',ord:1},{id:'s1',t:'w',x:0,y:0,title:'드라마1',kind:'s',n:3,ord:2},{id:'m9',t:'w',x:0,y:0,title:'비밀영화',kind:'m',ord:3});
 const G=(id,title,x,y,w,h,m)=>{const n={id,t:'c',x,y,w,h,title,col:'#6541F2',op:8,m,ph:true};S.nodes.push(n);mk(n)};
 G('G0','동아리',-500,-300,1100,800,['G1','e']);G('G1','문예부',-350,-150,500,300,['a','b']);
 WS.clear();WS.add('m1');WS.add('s1_2');wsSave();S.view={x:cv.clientWidth/2,y:cv.clientHeight/2,k:1};applyView();select(null);drawLinks()}"""
VIEW="k=>{S.view={x:cv.clientWidth/2,y:cv.clientHeight/2,k};applyView()}"
def q(pg,t):pg.fill('#dl [data-fq]',t);settle(pg,80)
ids=lambda pg:pg.evaluate("[...document.querySelectorAll('#dl [data-fp]')].map(b=>b.dataset.fp)")
txt=lambda pg:pg.inner_text('#dl [data-fr]')
def cen(pg,i):   # 인물 아이콘 가운데가 화면(캔버스) 가운데에서 얼마나 떨어졌는지, 지금 배율
    return pg.evaluate("i=>{const r=els[i].querySelector('.im').getBoundingClientRect(),c=cv.getBoundingClientRect();return [r.x+r.width/2-(c.left+c.width/2),r.y+r.height/2-(c.top+c.height/2),S.view.k]}",i)
def at(pg,i):
    dx,dy,k=cen(pg,i);return abs(dx)<3 and abs(dy)<3 and abs(k-1.3)<.01
def rzw(pg,k):   # 선택된 그룹의 크기 핸들이 화면에서 차지하는 너비
    pg.evaluate(VIEW,k);settle(pg,150);return pg.evaluate("document.querySelector('.n.c.sel .rz').getBoundingClientRect().width")
with sync_playwright() as p:
    b=p.chromium.launch();A=client(b,"")
    A.goto(EDIT);settle(A,700);A.evaluate(SETUP);settle(A,300)
    A.click('#bsr');settle(A,150)
    ok('F1 검색 버튼을 누르면 검색창이 뜨고 입력칸에 바로 커서가 감',A.evaluate("dl.style.display=='block'&&dlKind=='find'&&document.activeElement.matches('[data-fq]')"))
    q(A,'서')
    ok('F2 철자가 들어간 인물만 드롭다운에 나옴(김서준·서연)',sorted(ids(A))==['a','e'])
    q(A,'ALICE');r1=ids(A);q(A,'김 서준');r2=ids(A);q(A,'alicekim');r3=ids(A)
    ok('F3 대소문자·띄어쓰기는 무시하고 찾음',r1==['d'] and r2==['a'] and r3==['d'])
    q(A,'없는이름')
    ok('F4 결과가 없으면 안내 문구',ids(A)==[] and '검색 결과가 없어요' in txt(A))
    q(A,'')
    ok('F5 입력을 지우면 안내 문구만 보임',ids(A)==[] and '일부를 입력' in txt(A))
    q(A,'서');A.click('#dl [data-fp="e"]');settle(A,1000)
    ok('F6 목록에서 인물을 누르면 그 인물이 화면 가운데로 오고 배율 1.3',at(A,'e'))
    ok('F7 이동한 인물이 잠깐 강조되고(found) 곧 풀림',A.evaluate("els.e.classList.contains('found')") and (settle(A,1100) or True) and not A.evaluate("els.e.classList.contains('found')"))
    A.evaluate(VIEW,3);q(A,'박도윤');A.keyboard.press('Enter');settle(A,1000);out=at(A,'c')
    A.evaluate(VIEW,.2);q(A,'alice kim');A.keyboard.press('Enter');settle(A,1000)
    ok('F8 철자를 정확히 입력하고 Enter: 배율 3 에서는 줌아웃, 0.2 에서는 줌인으로 1.3 에 도착',out and at(A,'d'))
    A.evaluate(VIEW,1);q(A,'서');A.keyboard.press('Enter');settle(A,1000)
    ok('F9 똑같은 이름이 없으면 Enter 가 목록 첫 인물로 이동',at(A,'a'))
    q(A,'문예')
    ok('F10 그룹 이름을 검색하면 그 그룹에 속한 인물을 보여 줌',ids(A)==['a','b'] and '그룹 문예부' in txt(A))
    q(A,'동아리')
    ok('F11 큰 그룹은 안에 든 작은 그룹의 인물까지 보여 줌',sorted(ids(A))==['a','b','e'])
    q(A,'영화1')
    ok('F12 작품 이름을 검색하면 그 작품에 나오는 인물을 보여 줌',ids(A)==['a','b'] and '작품 영화1' in txt(A))
    q(A,'드라마')
    ok('F13 드라마는 어느 에피소드든 나오는 인물을 모두 보여 줌(편집 모드)',sorted(ids(A))==['c','d'])
    q(A,'비밀')
    ok('F14 편집 모드에선 안 본 작품도 검색됨',ids(A)==['f'])
    q(A,'onerror')
    ok('F15 이름에 HTML 이 들어 있어도 글자로만 보임',ids(A)==['f'] and A.evaluate("!document.querySelector('#dl img')&&window.__x===undefined"))
    A.evaluate(VIEW,1);v0=A.evaluate("[S.view.x,S.view.k]");q(A,'서')
    A.evaluate("document.querySelector('#dl [data-fq]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',isComposing:true,bubbles:true,cancelable:true}))");settle(A,900)
    ok('F16 한글 입력 중(조합 중) Enter 는 검색하지 않음',A.evaluate("[S.view.x,S.view.k]")==v0)
    A.evaluate(VIEW,.3);q(A,'박도윤');A.keyboard.press('Enter');settle(A,120)
    A.evaluate("zoomAt(cv.clientWidth/2,cv.clientHeight/2,1)");k1=A.evaluate('S.view.k');settle(A,900);k2=A.evaluate('S.view.k')
    ok('F17 이동 중에 휠·끌기를 하면 이동이 거기서 멈춤',abs(k1-k2)<1e-9 and k2<1.29)
    A.evaluate("dlShow('')");A.click('#bsr');settle(A,100);A.click('#dl [data-fq]');A.keyboard.press('Escape');settle(A,100)
    ok('F18 입력칸에서 Esc 를 누르면 검색창이 닫힘',A.evaluate("dl.style.display")=='none')
    # ── 읽기 모드(스포일러): 안 본 작품·숨은 인물은 검색에도 안 나옴
    A.evaluate("dlShow('')");A.click('#bm');settle(A,300)
    ok('R1 읽기 모드에도 검색 버튼이 보임',A.is_visible('#bsr'))
    A.click('#bsr');settle(A,150)
    q(A,'비밀');a1=txt(A);q(A,'alice');a2=ids(A);q(A,'드라마');a3=ids(A);q(A,'영화1');a4=ids(A)
    ok('R2 읽기 모드: 안 본 작품·그 작품에만 나오는 숨은 인물은 검색해도 안 나옴',('검색 결과가 없어요' in a1) and a2==[] and a3==['c'] and a4==['a','b'])
    A.evaluate(VIEW,1);q(A,'서연');A.keyboard.press('Enter');settle(A,1000)
    ok('R3 읽기 모드에서도 검색한 인물로 이동함',at(A,'e'))
    # ── 좁은 화면: 선택하면 검색창이 닫혀 인물이 가려지지 않음
    M=client(b,"");M.set_viewport_size({'width':500,'height':800})
    M.goto(EDIT);settle(M,700);M.evaluate(SETUP);settle(M,300)
    M.click('#bsr');settle(M,150);q(M,'박도윤');M.click('#dl [data-fp="c"]');settle(M,900)
    ok('M1 좁은 화면(500px)에선 인물을 고르면 검색창이 닫히고 그 인물로 이동',M.evaluate("dl.style.display")=='none' and at(M,'c'))
    # ── 그룹 크기 핸들: 화면에서 보이는 크기가 배율과 무관, 좁은 화면에선 더 큼
    A.evaluate("dlShow('')");A.click('#bm');settle(A,300);A.evaluate("select('G1')");settle(A,200)
    w1,w05,w2=rzw(A,1),rzw(A,.5),rzw(A,2)
    ok('H1 그룹 크기 핸들은 확대하면 커지고 축소하면 작아지되, 배율(2배·0.5배)만큼 그대로 따라가진 않음',w05<w1<w2 and w2<1.8*w1 and w05>.6*w1 and 12<w1<28)
    pos=A.evaluate("""(()=>{const g=nd('G1'),r=document.querySelector('.n.c.sel .rz').getBoundingClientRect(),c=cv.getBoundingClientRect(),v=S.view;return [r.x+r.width/2-(c.left+v.x+(g.x+2+g.w*.8536)*v.k),r.y+r.height/2-(c.top+v.y+(g.y+2+g.h*.8536)*v.k)]})()""")
    ok('H2 핸들 가운데는 원 둘레(오른쪽 아래 45도)에 그대로 있음',abs(pos[0])<2.5 and abs(pos[1])<2.5)
    M.evaluate("select('G1')");settle(M,200);wm=rzw(M,1)
    ok('H3 좁은 화면(500px)에선 핸들이 더 큼',wm>w1*1.3)
    A.evaluate("(()=>{const n={id:'G3',t:'c',x:900,y:900,w:120,h:120,title:'작은',col:'#6541F2',op:8,m:[],ph:true};S.nodes.push(n);mk(n)})()")
    A.evaluate(VIEW,.08);A.evaluate("select(null);select('G3')");settle(A,150)
    wt=A.evaluate("document.querySelector('.n.c.sel .rz').getBoundingClientRect().width");gw=A.evaluate("nd('G3').w*S.view.k")
    ok('H4 가장 작은 원(120)을 아주 줄여 보면 핸들이 원 너비의 1/4 정도까지만 작아짐(원을 덮지 않음)',wt<gw*.25+5)
    A.evaluate(VIEW,1);A.evaluate("select(null);select('G1')");settle(A,200)
    bb=A.evaluate("(()=>{const r=document.querySelector('.n.c.sel .rz').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()");w0=A.evaluate("nd('G1').w")
    A.mouse.move(*bb);A.mouse.down();A.mouse.move(bb[0]+50,bb[1]+30,steps=6);A.mouse.up();settle(A,200)
    ok('H5 새 핸들을 끌면 그룹 크기가 그대로 조절됨',A.evaluate("nd('G1').w")>w0+40)
    A.evaluate("select(null);select('G1')");settle(A,200)
    bb=A.evaluate("(()=>{const r=document.querySelector('.n.c.sel .rz').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()");g0=A.evaluate("[nd('G1').w,nd('G1').h]")
    A.keyboard.down('Control');A.mouse.move(*bb);A.mouse.down();A.mouse.move(bb[0]+50,bb[1]+30,steps=6);A.mouse.up();A.keyboard.up('Control');settle(A,200)
    g1=A.evaluate("[nd('G1').w,nd('G1').h]");want=(g0[0]+g0[1])/2+40*1.17
    ok('H6 Ctrl 을 누르고 핸들을 끌면 정원(가로=세로)이 됨(평균 크기에서 대각선으로 늘어남), 안 누르면 타원 그대로',abs(g1[0]-g1[1])<.01 and abs(g1[0]-want)<2 and abs(g0[0]-g0[1])>50)
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    b.close()
