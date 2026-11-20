from helpers import *
# 편집 모드: 빈 곳을 좌클릭으로 끌면 사각형 범위 다중 선택(함께 이동·삭제·실행 취소), 방 동기화
EDIT='http://localhost:8765/index.html?mode=edit'
SETUP="""()=>{S.nodes=[];S.links=[];W.querySelectorAll('.n,.lb').forEach(x=>x.remove());els={};lels={};
 [['a',-200,-100],['b',0,-100],['c',200,-100],['d',200,200]].forEach(([i,x,y])=>{const n={id:i,t:'p',x,y,name:i,desc:'',img:'',col:'#0066FF'};S.nodes.push(n);mk(n)});
 addLink('a','b');select(null);drawLinks()}"""
pt=lambda pg,x,y:pg.evaluate("([x,y])=>{const r=cv.getBoundingClientRect();return [r.left+S.view.x+x*S.view.k,r.top+S.view.y+y*S.view.k]}",[x,y])
ms=lambda pg:sorted(pg.evaluate("[...msel]"))
pos=lambda pg:pg.evaluate("S.nodes.map(n=>[n.id,Math.round(n.x),Math.round(n.y)])")
view=lambda pg:pg.evaluate("[S.view.x,S.view.y]")
def box(pg,a,b,mid=None):
    (x0,y0),(x1,y1)=pt(pg,*a),pt(pg,*b);pg.mouse.move(x0,y0);pg.mouse.down();pg.mouse.move(x1,y1,steps=8)
    r=pg.eval_on_selector('#sbox','e=>getComputedStyle(e).display')!='none';pg.mouse.up();pg.wait_for_timeout(200);return r
with sync_playwright() as p:
    b=p.chromium.launch();A=client(b,"")
    A.goto(EDIT);settle(A,700);A.evaluate(SETUP);settle(A,300)
    v0=view(A);shown=box(A,(-300,-250),(330,60))
    ok('M1 빈 곳을 끌면 사각형이 보이고 안에 든 인물 3명이 선택됨(화면은 안 움직임)',shown and ms(A)==['a','b','c'] and A.evaluate("document.querySelectorAll('.n.ms').length")==3 and view(A)==v0)
    ok('M2 사각형이 끝나면 사각형은 사라지고 "3개 선택됨" 패널이 뜸',A.eval_on_selector('#sbox','e=>getComputedStyle(e).display')=='none' and '3개 선택됨' in A.inner_text('#ins'))
    x,y=A.evaluate("(()=>{const r=els.b.querySelector('.im').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()");k=A.evaluate('S.view.k')
    A.mouse.move(x,y);A.mouse.down();A.mouse.move(x+60,y+30,steps=6);A.mouse.up();settle(A,300);q=dict((i,(a,c)) for i,a,c in pos(A))
    ok('M3 선택한 것 하나를 끌면 3명이 함께 움직이고 선택 안 한 d 는 그대로',q['a'][0]>-200 and q['b'][0]>0 and q['c'][0]>200 and q['a'][0]-(-200)==q['c'][0]-200 and q['d']==(200,200))
    A.keyboard.press('Delete');settle(A,300)
    ok('M4 Delete 로 선택한 3명이 지워지고 이어진 선도 함께 사라짐(d 는 남음)',A.evaluate("S.nodes.map(n=>n.id)")==['d'] and A.evaluate('S.links.length')==0 and not A.evaluate("!!els.a"))
    A.keyboard.press('Control+z');settle(A,500)
    ok('M5 실행 취소(Ctrl+Z)로 한꺼번에 되살아남',A.evaluate("S.nodes.map(n=>n.id).sort().join()")=='a,b,c,d' and A.evaluate('S.links.length')==1)
    box(A,(-120,-130),(-90,-40))
    ok('M6 인물 하나만 걸치면 보통 선택(인물 패널)',A.evaluate('sel')=='a' and ms(A)==[] and '인물' in A.inner_text('#ins'))
    box(A,(-300,-250),(330,60));A.mouse.click(*pt(A,-300,330));settle(A,200)
    ok('M7 빈 곳을 클릭하면 다중 선택이 풀림',ms(A)==[] and A.evaluate("document.querySelectorAll('.n.ms').length")==0)
    # ── 방 안에서도 같이 지워지고 되돌려짐
    B=client(b,"");A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    B.goto(EDIT+h);settle(B,1800)
    box(A,(-300,-150),(430,60));A.keyboard.press('Delete');settle(A,1500)
    ok('M8 방 안에서 여러 명을 지우면 다른 사람 화면·서버에도 반영됨',B.evaluate("S.nodes.map(n=>n.id).join()")=='d' and same(A,B,room=room))
    A.keyboard.press('Control+z');settle(A,1800)
    ok('M9 방 안에서 실행 취소하면 모두 되살아남',B.evaluate("S.nodes.length")==4 and same(A,B,room=room))
    got=lambda:sorted(set(ms(A))|({A.evaluate('sel')}-{None}))   # 한 명만 걸치면 다중 선택이 아니라 단일 선택이 됨
    # 사각형 선택은 인물 아이콘 원(반지름 42)에 닿을 때만: 글자 영역·원 밖 네모 모서리는 해당 없음
    A.evaluate(SETUP);A.evaluate("S.view={x:cv.clientWidth/2,y:cv.clientHeight/2,k:1};applyView();nd('b').name='가나다라마바사아자차';upd(nd('b'));select(null)");settle(A,200)
    box(A,(115,-98),(185,-70));t1=got();A.evaluate("select(null)")
    ok('M9 사각형이 인물 이름·설명 글자 위만 지나면 선택되지 않음',t1==[])
    box(A,(-30,-130),(8,-92));t2=got();A.evaluate("select(null)")
    ok('M10 사각형이 아이콘의 네모 모서리(원 밖)만 스치면 선택되지 않음',t2==[])
    box(A,(-30,-130),(20,-70));t3=got();A.evaluate("select(null)")
    ok('M11 사각형이 아이콘 원에 닿으면 선택됨',t3==['b'])
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    b.close()
