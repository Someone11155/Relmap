from helpers import *
# 그룹 안에 다른 그룹 포함: 자동 소속(작은 원이 안에 들어오면), 함께 이동, 밖으로 끌면 제외, 쌓이는 순서, 읽기 모드 숨김, 검증, 방 동기화
BASE='http://localhost:8765/index.html'
EDIT=BASE+'?mode=edit'
SETUP="""()=>{S.nodes=S.nodes.filter(n=>n.t!='w');[...S.nodes].forEach(n=>delOne(n.id));S.view={x:cv.clientWidth/2,y:cv.clientHeight/2,k:1};applyView();select(null);
 S.nodes.push({id:'m1',t:'w',x:0,y:0,title:'영화1',kind:'m',ord:1});
 const n={id:'G1',t:'c',x:-350,y:-250,w:700,h:500,title:'큰 그룹',col:'#6541F2',op:8,m:[],ph:true};S.nodes.push(n);mk(n);sv()}"""
org=lambda pg:pg.evaluate("[cv.getBoundingClientRect().left+S.view.x,cv.getBoundingClientRect().top+S.view.y]")
inner=lambda pg:pg.evaluate("S.nodes.find(n=>n.t=='c'&&n.id!='G1').id")
def drag(pg,x,y,dx,dy):
    pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x+dx,y+dy,steps=10);pg.mouse.up();settle(pg,300)
with sync_playwright() as p:
    b=p.chromium.launch();pg=client(b,"")
    pg.goto(EDIT);settle(pg,700);pg.evaluate(SETUP);pg.click('[data-t=c]');settle(pg,300);gi=inner(pg)
    ok('N1 큰 그룹 안쪽에 새 그룹을 만들면 자동으로 큰 그룹의 멤버가 됨',pg.evaluate("g=>nd('G1').m.includes(g)",gi) and pg.evaluate("g=>!nd(g).m.includes('G1')",gi))
    ok('N2 작은 원은 큰 원 패널의 멤버 목록에 있고, 큰 원은 작은 원 패널에 없음(서로 포함 방지)',(pg.evaluate("select('G1')")or True) and pg.locator('#ins [data-mem="%s"]'%gi).count()==1 and (pg.evaluate("g=>select(g)",gi)or True) and pg.locator('#ins [data-mem="G1"]').count()==0)
    ok('N3 작은 원이 큰 원 위에 보이도록 화면 순서가 맞음',pg.evaluate("g=>!!(els.G1.compareDocumentPosition(els[g])&Node.DOCUMENT_POSITION_FOLLOWING)",gi))
    pg.evaluate("select(null)");ox,oy=org(pg);drag(pg,ox+300,oy,100,50)
    ok('N4 큰 그룹을 끌면 안에 든 작은 그룹도 함께 움직이고 계속 멤버로 남음',pg.evaluate("g=>nd('G1').x==-250&&nd('G1').y==-200&&nd(g).x==-110&&nd(g).y==-160&&nd('G1').m.includes(g)",gi))
    ox,oy=org(pg);cx,cy=ox+100,oy+50;drag(pg,cx,cy,450,250)
    ok('N5 작은 그룹을 큰 그룹 밖으로 끌어내면 멤버에서 빠짐',pg.evaluate("g=>!nd('G1').m.includes(g)",gi))
    pg.evaluate("g=>{const n=nd(g);n.x=-110;n.y=-160;upd(n);joinG(n)}",gi)
    ok('N6 다시 안으로 들이면 다시 멤버가 됨',pg.evaluate("g=>nd('G1').m.includes(g)",gi))
    pg.evaluate("select(null)");cx,cy=pg.evaluate("g=>{const r=els[g].getBoundingClientRect();return[r.left+r.width/2,r.top+r.height/2]}",gi)
    hot=lambda:pg.evaluate("els.G1.classList.contains('hot')")
    h0=hot();pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move(cx+10,cy+10,steps=4);h1=hot();pg.mouse.move(cx+900,cy+500,steps=8);h2=hot();pg.mouse.move(cx+10,cy+10,steps=8);h3=hot();pg.mouse.up();settle(pg,300)
    ok('N6b 작은 그룹을 큰 그룹 안으로 끌 때만 큰 그룹에 파란 테두리, 놓으면 사라짐',[h0,h1,h2,h3,hot()]==[False,True,False,True,False] and pg.evaluate("g=>nd('G1').m.includes(g)",gi))
    pg.evaluate("[...S.nodes].filter(n=>n.t=='c').forEach(n=>delOne(n.id));const g=(id,x,y,w,h)=>{const n={id,t:'c',x,y,w,h,title:id,col:'#6541F2',op:8,m:[],ph:true};S.nodes.push(n);mk(n)};g('small',-100,-100,200,200);g('big',-300,-300,600,600)")
    ok('N7 작은 원을 먼저 만들고 큰 원을 나중에 만들어도 큰 원이 아래에 깔림',pg.evaluate("!!(els.big.compareDocumentPosition(els.small)&Node.DOCUMENT_POSITION_FOLLOWING)"))
    # 작은 그룹 안의 인물은 큰 그룹을 끌어도 작은 그룹과 함께 움직이고 계속 작은 그룹의 멤버
    pg.evaluate("S.nodes.push({id:'pk',t:'p',x:-42,y:-42,name:'K',desc:'',img:'',col:'#0066FF'});mk(nd('pk'));nd('small').m=['pk'];nd('big').m=['small'];sv();select(null)")
    ox,oy=org(pg);drag(pg,ox-250,oy,100,50)
    ok('N10 큰 그룹을 끌면 안에 든 작은 그룹의 인물도 함께 움직이고 작은 그룹에 남음',pg.evaluate("nd('big').x==-200&&nd('small').x==0&&nd('pk').x==58&&nd('pk').y==8&&nd('small').m.includes('pk')&&inside(nd('small'),nd('pk'))"))
    # 큰 그룹의 크기를 줄이면 안의 인물·작은 그룹도 같은 비율로 따라와서 밖으로 밀려나지 않음
    pg.evaluate("select('big')");settle(pg,150);rz=pg.locator('.n.c[data-id="big"] .rz').bounding_box();sw0=pg.evaluate("nd('small').w")
    pg.mouse.move(rz['x']+8,rz['y']+8);pg.mouse.down();pg.mouse.move(rz['x']-192,rz['y']-192,steps=10);pg.mouse.up();settle(pg,300)
    ok('N11 큰 그룹을 줄이면 안의 인물·작은 그룹이 같은 비율로 따라와 모두 그대로 안에 있음',pg.evaluate("[nd('big').w<400,inside(nd('big'),nd('pk')),gIn(nd('big'),nd('small')),nd('big').m.includes('small'),nd('small').m.includes('pk'),inside(nd('small'),nd('pk')),nd('small').w<arguments[0]]".replace('arguments[0]',str(sw0)))==[True]*7)
    pg.evaluate("select(null)")
    # 읽기 모드 숨김: 안 본 작품의 인물만 든 작은 그룹과 그걸 품은 큰 그룹이 함께 숨고, 보면 함께 나타남
    pg.evaluate("[...S.nodes].filter(n=>n.t=='c').forEach(n=>delOne(n.id))");pg.evaluate(SETUP);pg.click('[data-t=c]');settle(pg,300);gi=inner(pg)
    pg.evaluate("S.nodes.push({id:'p1',t:'p',x:-30,y:-30,name:'P',desc:'',img:'',col:'#0066FF',tg:['m1']});mk(nd('p1'));joinGroups(nd('p1'));sv()")
    pg.click('#bm');settle(pg,400)
    hid=pg.evaluate("g=>[HID.has('p1'),HID.has(g),HID.has('G1')]",gi)
    pg.evaluate("WS.add('m1');drawLinks()");settle(pg,200)
    ok('N8 읽기 모드: 안 본 작품의 인물만 든 작은 그룹·큰 그룹이 함께 숨고, 보면 함께 나타남',hid==[True,True,True] and pg.evaluate("g=>[HID.has('p1'),HID.has(g),HID.has('G1')]",gi)==[False,False,False])
    r=pg.evaluate("cleanDoc({nodes:[{id:'g1',t:'c',w:300,h:300,m:['g2','zzz']},{id:'g2',t:'c',w:100,h:100,m:[]}],links:[]}).nodes[0].m")
    ok('N9 불러온 파일: 그룹 id 도 멤버로 인정, 없는 id 는 걸러냄',r==['g2'])
    # 방 안 동기화
    A=client(b,"");B=client(b,"")
    A.goto(EDIT);settle(A,500);A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    B.goto(BASE+h);settle(B,1800)
    A.evaluate(SETUP);A.click('[data-t=c]');settle(A,300);gi=inner(A);settle(A,1800)
    ok('R1 방: 그룹 안의 그룹 관계가 B·DB 에 똑같이 반영됨',same(A,B,room=room) and B.evaluate("g=>nd('G1').m.includes(g)",gi))
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    b.close()
