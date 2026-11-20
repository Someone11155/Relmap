from helpers import *
# 패널을 다시 그려도 스크롤 위치 유지(패널·등장 작품 드롭다운), 인물 아이콘 크기(버튼 3개·가운데 유지·선·사각형 선택·검증·방 동기화)
EDIT='http://localhost:8765/index.html?mode=edit'
SETUP="""()=>{S.nodes=[];S.links=[];W.querySelectorAll('.n,.lb').forEach(x=>x.remove());els={};lels={};
 [['a',-200,-100],['b',100,-100]].forEach(([i,x,y])=>{const n={id:i,t:'p',x,y,name:i,desc:'',img:'',col:'#0066FF'};S.nodes.push(n);mk(n)});
 for(let i=0;i<40;i++)S.nodes.push({id:'m'+i,t:'w',x:0,y:0,title:'영화'+i,kind:'m',ord:i});
 nd('a').dx=Array.from({length:8},(_,i)=>({t:'설명'+i,g:''}));
 addLink('a','b');S.view={x:cv.clientWidth/2,y:cv.clientHeight/2,k:1};applyView();select(null);drawLinks()}"""
slide=lambda pg,v:pg.click(f'#ins [data-is="{v}"]')   # 크기 버튼(작게 56 · 중간 84 · 크게 120)
with sync_playwright() as p:
    b=p.chromium.launch();A=client(b,"")
    A.goto(EDIT);settle(A,700);A.evaluate(SETUP);settle(A,300)
    # ── 스크롤 유지
    A.evaluate("select('a')");settle(A,200)
    A.click('[data-tgd]');settle(A,150)
    A.evaluate("(()=>{ins.scrollTop=ins.scrollHeight;document.querySelector('.ddl').scrollTop=150})()");settle(A,100)
    s0=A.evaluate("[ins.scrollTop,document.querySelector('.ddl').scrollTop]")
    A.evaluate("document.querySelectorAll('.ddl [data-tg]')[30].click()");settle(A,200)
    s1=A.evaluate("[ins.scrollTop,document.querySelector('.ddl').scrollTop]")
    ok('I1 드롭다운에서 작품을 체크해도 패널·드롭다운 목록 스크롤이 맨 위로 안 올라감',s0[0]>50 and s0[1]>50 and s1==s0 and A.evaluate("nd('a').tg.length")==1)
    A.evaluate("select('b')");settle(A,200)
    ok('I2 다른 인물을 고르면 패널은 맨 위에서 시작',A.evaluate("ins.scrollTop")==0)
    # ── 아이콘 크기
    A.evaluate("select('a')");settle(A,200)
    c0=A.evaluate("[nd('a').x+42,nd('a').y+42]");slide(A,120);settle(A,150)
    ok('I3 크게 버튼을 누르면 아이콘이 그만큼 커지고 가운데는 그대로(저장은 is)',A.evaluate("[document.querySelector('.n[data-id=a] .im').offsetWidth,nd('a').is,nd('a').x+ir(nd('a')),nd('a').y+ir(nd('a'))]")==[120,120,c0[0],c0[1]])
    d=A.evaluate("(()=>{const l=svg.querySelector('line'),r=ir(nd('a')),c=ctr(nd('a'));return Math.hypot(+l.getAttribute('x1')-c[0],+l.getAttribute('y1')-c[1])-r})()")
    ok('I4 관계선이 커진 아이콘 가장자리에서 시작함(바깥 6px)',abs(d-6)<.5)
    slide(A,56);settle(A,100);sm=A.evaluate("[document.querySelector('.n[data-id=a] .im').offsetWidth,document.querySelector('#ins [data-is=\"56\"]').classList.contains('on')]")
    slide(A,84);settle(A,100)
    ok('I5 작게는 56, 중간(84)으로 되돌리면 저장값에서 빠짐',sm==[56,True] and A.evaluate("nd('a').is")is None)
    slide(A,120);A.evaluate("select(null)");settle(A,150)
    def box(a,bb):
        (x0,y0),(x1,y1)=[A.evaluate("([x,y])=>{const r=cv.getBoundingClientRect();return [r.left+S.view.x+x,r.top+S.view.y+y]}",q) for q in(a,bb)]
        A.mouse.move(x0,y0);A.mouse.down();A.mouse.move(x1,y1,steps=6);A.mouse.up();settle(A,150)
    cx,cy=A.evaluate("[nd('a').x+60,nd('a').y+60]")
    box((cx+45,cy-70),(cx+75,cy-48));t1=A.evaluate("sel")
    ok('I6 사각형 선택: 큰 아이콘도 원 밖 네모 모서리는 빗나감',t1 is None)
    box((cx+40,cy-15),(cx+80,cy+15));t2=A.evaluate("sel")
    ok('I7 사각형 선택: 큰 아이콘 원 안쪽(반지름 60 안)에 닿으면 선택됨',t2=='a')
    r=A.evaluate("cleanDoc({nodes:[{id:'a',t:'p',is:5},{id:'b',t:'p',is:'x'},{id:'c',t:'p',is:84},{id:'d',t:'p',is:1e9},{id:'e',t:'p',is:120.4}],links:[]}).nodes.map(n=>n.is)")
    ok('I8 불러온 파일의 아이콘 크기: 범위(24~400) 밖은 맞추고, 기본값·이상한 값은 저장 안 함',r==[24,None,None,400,120])
    A.evaluate("select(null);nd('a').tg=[]");A.click('#bm');settle(A,300)
    ok('I9 읽기 모드에서도 같은 크기로 보임',A.evaluate("document.querySelector('.n[data-id=a] .im').offsetWidth")==120)
    A.click('#bm');settle(A,200)
    # ── 방 동기화
    B=client(b,"");A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    B.goto(EDIT+h);settle(B,1800)
    A.evaluate("select('b')");settle(A,200);slide(A,120);settle(A,1800)
    ok('I10 방: 아이콘 크기가 B 화면·DB 에 똑같이 반영됨',B.evaluate("nd('b').is")==120 and B.evaluate("document.querySelector('.n[data-id=b] .im').offsetWidth")==120 and same(A,B,room=room))
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    b.close()
