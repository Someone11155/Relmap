from helpers import *
# 읽기 모드 물리: 화면 전용(저장 위치 불변)·선 길이 거의 일정·움직임 범위 제한·잡아당길수록 덜 따라옴·놓으면 복귀
BASE='http://localhost:8765/index.html'      # 모드 지정 없음 = 읽기 모드
P='.n.p[data-id="b"] .im'
vis=lambda pg:pg.eval_on_selector('#ins','e=>getComputedStyle(e).display')!='none'
off=lambda pg,i:pg.evaluate("i=>{const n=nd(i);return Math.hypot(n._dx||0,n._dy||0)}",i)
home=lambda pg,a,b:pg.evaluate("([a,b])=>{const A=nd(a),B=nd(b);return Math.hypot(B.x-A.x,B.y-A.y)}",[a,b])
shown=lambda pg,a,b:pg.evaluate("([a,b])=>{const[x,y]=ctr(nd(a)),[u,v]=ctr(nd(b));return Math.hypot(u-x,v-y)}",[a,b])
maxoff=lambda pg:pg.evaluate("Math.max(0,...S.nodes.filter(n=>n.t=='p').map(n=>Math.hypot(n._dx||0,n._dy||0)))")
poss=lambda pg:pg.evaluate("JSON.stringify(S.nodes.map(n=>[n.id,n.x,n.y,n.w,n.h]))")
def ctr(pg,sel):
    bb=pg.locator(sel).bounding_box();return bb['x']+bb['width']/2,bb['y']+bb['height']/2
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_context(viewport={'width':1280,'height':760}).new_page();pg.on('pageerror',lambda e:ERR.append(str(e)))
    pg.goto(BASE);settle(pg,700)
    RL=pg.evaluate('RL');k=pg.evaluate('S.view.k');p0=poss(pg)
    ok('P0 읽기 모드로 시작',pg.evaluate('cv.dataset.mode')=='r')
    x,y=ctr(pg,P);pg.mouse.move(x,y);pg.mouse.down()
    got=[];prev=0
    for px in [30,60,120,240,480,900]:
        pg.mouse.move(x+px,y,steps=8);settle(pg,600);got.append((px/k,off(pg,'b')))
    print('INFO 당긴 양(월드)→움직인 양',[(round(d),round(o,1)) for d,o in got],'RL',RL)
    sl=[(got[i][1]-got[i-1][1])/(got[i][0]-got[i-1][0]) for i in range(1,len(got))]
    ok('P1 처음엔 거의 1:1로 따라오다 점점 덜 따라옴(기울기가 계속 줄어듦)',got[0][1]>0.7*got[0][0] and all(sl[i]>sl[i+1] for i in range(len(sl)-1)) and sl[-1]>=0)
    ok('P2 아무리 당겨도 움직임 범위가 제한값(RL) 이내',got[-1][1]<=RL*1.001 and maxoff(pg)<=RL*1.5)
    ok('P3 연결된 인물도 따라 움직임',off(pg,'c')>3 and off(pg,'d')>3)
    rel=[abs(shown(pg,a,c)-home(pg,a,c))/home(pg,a,c) for a,c in [('b','c'),('b','d')]]
    print('INFO 선 길이 변화율',[round(r*100,2) for r in rel])
    ok('P4 선 길이가 거의 안 변함(3% 이내)',max(rel)<.03)
    gm=pg.evaluate("""()=>{const c=nd('a'),e=els.a.style,L=parseFloat(e.left),T=parseFloat(e.top),w=parseFloat(e.width),h=parseFloat(e.height);
      return {sh:Math.hypot(L+w/2-(c.x+c.w/2),T+h/2-(c.y+c.h/2)),dw:w-c.w,mem:c.m.length,inside:c.m.map(nd).every(p=>{const[x,y]=ctr(p);return((x-L-w/2)/(w/2))**2+((y-T-h/2)/(h/2))**2<=1.05})}}""")
    print('INFO 그룹 원 중심 이동',round(gm['sh'],1),'크기 변화',round(gm['dw'],1),'멤버',gm['mem'])
    ok('P4b 그룹 원이 멤버들을 따라 위치·크기가 바뀌고 멤버를 모두 감쌈',gm['mem']>0 and gm['sh']>1 and abs(gm['dw'])>.5 and gm['inside'])
    pg.evaluate('sv()');settle(pg,500)
    ok('P5 저장 위치·브라우저 저장본에 임시 움직임이 섞이지 않음',poss(pg)==p0 and '_dx' not in (pg.evaluate("localStorage.getItem('relmap_v1')") or ''))
    pg.mouse.up();pg.evaluate('window.__m=[]');settle(pg,3000)
    ok('P6 놓으면 인물·그룹 원이 원래 자리·크기로 돌아옴',maxoff(pg)<.5 and pg.evaluate("(()=>{const c=nd('a'),e=els.a.style;return e.left==c.x+'px'&&e.top==c.y+'px'&&e.width==c.w+'px'&&e.height==c.h+'px'})()") and pg.evaluate("document.querySelector('.n.p[data-id=b]').style.translate")=='' and poss(pg)==p0)
    # 짧게 누르면 프로필, 움직임 없음
    pg.click(P);settle(pg,300)
    ok('P7 짧게 누르면 프로필이 뜨고 인물은 안 움직임',vis(pg) and maxoff(pg)==0)
    # 편집 모드로 바꾸면 임시 움직임이 사라짐
    x,y=ctr(pg,P);pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x+100,y,steps=6);settle(pg,200);pg.mouse.up();pg.click('#bm');settle(pg,100)
    ok('P8 편집 모드로 바꾸면 임시 움직임이 즉시 사라짐',maxoff(pg)==0 and pg.evaluate("[...document.querySelectorAll('.n.p')].every(e=>e.style.translate==='')"))
    ok('P8b 편집 모드에는 물리 버튼(물리 ON/OFF, ↻)이 없음',not pg.is_visible('#bp') and not pg.is_visible('#bh'))
    pg.evaluate("()=>{const b=nd('b'),c=nd('c');b.x=c.x+10;b.y=c.y+10;upd(b);heat(1)}");settle(pg,2000)
    ok('P8c 편집 모드에선 겹쳐 놓아도 자동으로 밀어내지 않음(물리 꺼짐)',pg.evaluate("(()=>{const b=nd('b'),c=nd('c');return b.x==c.x+10&&b.y==c.y+10&&alpha==0})()"))
    pg.click('#bm');settle(pg,200)
    # 큰 그래프(허브 1 + 가장자리 24, 고리 연결)에서도 안정적인지
    pg.evaluate("""()=>{const N=[{id:'h',t:'p',x:0,y:0,name:'H',desc:'',img:'',col:'#0066FF'}],L=[];
      for(let i=0;i<24;i++){const a=i/24*Math.PI*2;N.push({id:'q'+i,t:'p',x:Math.cos(a)*300,y:Math.sin(a)*300,name:'Q'+i,desc:'',img:'',col:'#6541F2'});
        L.push({id:'a'+i,a:'h',b:'q'+i,label:'',col:'#70737C',w:5,o:30});L.push({id:'r'+i,a:'q'+i,b:'q'+((i+1)%24),label:'',col:'#70737C',w:5,o:30})}
      S={view:null,ph:true,nodes:N,links:L};W.querySelectorAll('.n,.lb').forEach(x=>x.remove());els={};lels={};hov=null;S.nodes.forEach(mk);select(null);fit();rreset()}""")
    settle(pg,300);x,y=ctr(pg,'.n.p[data-id="h"] .im');pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x+600,y+200,steps=10);settle(pg,1000)
    m=maxoff(pg);fin=pg.evaluate("S.nodes.every(n=>Number.isFinite(n._dx)&&Number.isFinite(n._dy))")
    pg.mouse.up();settle(pg,4000)
    print('INFO 큰 그래프 최대 움직임',round(m,1),'복귀 후',round(maxoff(pg),2))
    ok('P9 큰 그래프에서도 값이 안정적(범위 이내·계산 오류 없음)과 놓으면 복귀',fin and m<=RL*1.5 and maxoff(pg)<.5)
    ok('Z 페이지 오류 없음',not ERR)
    b.close()
