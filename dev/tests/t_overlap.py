import time
from playwright.sync_api import sync_playwright
URL='http://localhost:8765/index.html?mode=edit'
ok=lambda n,v:print(('PASS ' if v else 'FAIL ')+n)
def lab(pg,text): return pg.locator('.lb',has_text=text)
def op(pg,text): return float(pg.evaluate("t=>{const e=[...document.querySelectorAll('.lb')].find(x=>x.textContent==t);return getComputedStyle(e).opacity}",text))
def ov(pg,text): return pg.evaluate("t=>[...document.querySelectorAll('.lb')].find(x=>x.textContent==t).classList.contains('ov')",text)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_context(viewport={'width':1280,'height':760}).new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL);pg.wait_for_timeout(700);pg.evaluate('alpha=0');pg.wait_for_timeout(500)
    # 샘플: '소꿉친구' 라벨이 김서준 설명 글자 위에 걸쳐 있음
    ok('1 겹쳐 있는 라벨(소꿉친구)이 반투명',ov(pg,'소꿉친구') and abs(op(pg,'소꿉친구')-.35)<.02)
    ok('2 겹치지 않는 라벨(라이벌)은 그대로 불투명',(not ov(pg,'라이벌')) and op(pg,'라이벌')==1)
    # 겹침 해소: 김서준을 아래로 멀리 이동
    bb=pg.locator('.p[data-id="b"] .im').bounding_box();x,y=bb['x']+42,bb['y']+42
    pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x-20,y+140,steps=10);pg.mouse.up();pg.evaluate('alpha=0');pg.wait_for_timeout(500)
    st1=ov(pg,'소꿉친구')
    # 다시 겹치게: 서준을 원래 위치 근처로
    pg.mouse.move(x-20,y+140);pg.mouse.down();pg.mouse.move(x,y,steps=10);pg.mouse.up();pg.evaluate('alpha=0');pg.wait_for_timeout(500)
    ok('3 드래그로 겹침이 풀리면 불투명, 다시 겹치면 반투명',(not st1) and ov(pg,'소꿉친구'))
    # 설명이 길어지면 새로 겹침: 박도윤(d)을 '소꿉친구' 라벨이 이름 줄 아래쪽에 오도록 배치
    pg.evaluate("""(()=>{nd('b').x=0;nd('b').y=1000;nd('c').x=800;nd('c').y=1000;upd(nd('b'));upd(nd('c'));nd('d').x=-2000;nd('d').y=-2000;upd(nd('d'));drawLinks()})()""");pg.wait_for_timeout(500)
    a0=ov(pg,'소꿉친구')
    pg.evaluate("""(()=>{const e=[...document.querySelectorAll('.lb')].find(x=>x.textContent=='소꿉친구'),lx=parseFloat(e.style.left),ly=parseFloat(e.style.top),d=nd('d');
      d.desc='';d.x=lx-98-40;d.y=ly-70;upd(d);drawLinks()})()""");pg.wait_for_timeout(500)
    a1=ov(pg,'소꿉친구')
    pg.evaluate("nd('d').desc='가나다라마바사 '.repeat(25);upd(nd('d'))");pg.wait_for_timeout(500)
    a2=ov(pg,'소꿉친구')
    pg.evaluate("nd('d').desc='';upd(nd('d'))");pg.wait_for_timeout(500)
    a3=ov(pg,'소꿉친구')
    ok('4 (다른 인물과 안 겹치는 상태에서) 설명이 비어 있으면 안 겹침 → 길어지면 반투명 → 지우면 다시 불투명',(not a0) and (not a1) and a2 and (not a3))
    # 선택된 라벨은 편집 중이므로 불투명 유지
    pg.evaluate("nd('b').x=nd('c').x-60;upd(nd('b'))");pg.wait_for_timeout(400)
    id_=pg.evaluate("[...document.querySelectorAll('.lb')].find(x=>x.textContent=='소꿉친구').dataset.id")
    pg.evaluate(f"select('{id_}')");pg.wait_for_timeout(400)
    ok('5 선택된(편집 중인) 라벨은 겹쳐도 불투명',op(pg,'소꿉친구')==1)
    pg.evaluate("select(null)");pg.wait_for_timeout(300)
    # 축소(lod)로 글자가 숨겨졌다가 돌아와도 다시 계산
    pg.evaluate("nd('b').x=nd('c').x-60;nd('b').y=nd('c').y;upd(nd('b'));drawLinks()");pg.wait_for_timeout(300)
    before=ov(pg,'소꿉친구')
    pg.evaluate("S.view.k=.4;applyView()");pg.wait_for_timeout(300);pg.evaluate("S.view.k=1;applyView()");pg.wait_for_timeout(500)
    ok('6 축소했다 돌아와도 상태가 올바름',before==ov(pg,'소꿉친구'))
    # 라벨/인물 그림자 상태에서 성능(인물 80, 선 120)
    pg.evaluate("""(()=>{const base=S.nodes.length;for(let i=0;i<80;i++){const n={id:'p'+i,t:'p',x:(i%10)*260-1200,y:Math.floor(i/10)*200+500,name:'인물'+i,desc:'설명 '+i,img:'',col:'#0066FF'};S.nodes.push(n);mk(n)}
      for(let i=0;i<120;i++){S.links.push({id:'q'+i,a:'p'+(i%80),b:'p'+((i*7+3)%80),label:'관계'+i,col:'#70737C',w:5,o:30})}drawLinks()})()""");pg.wait_for_timeout(800)
    t=pg.evaluate("(()=>{const t0=performance.now();for(let i=0;i<30;i++){drawLinks();ovCheck()}return (performance.now()-t0)/30})()")
    ok('7 인물 80·선 120에서 drawLinks+겹침검사 1회 %.1fms'%t,t<25)
    # ── 관계선 글자 크기: 확대·축소에 맞춰 바뀜(배율의 제곱근만큼), 좁은 화면에선 더 큼, 크기가 바뀌면 겹침 검사를 다시 함
    pg.evaluate("S.nodes=S.nodes.filter(n=>!/^p\d+$/.test(n.id));S.links=S.links.filter(l=>!/^q\d+$/.test(l.id));[...document.querySelectorAll('.n')].forEach(e=>{if(/^p\d+$/.test(e.dataset.id))e.remove()});drawLinks()")
    def lh(pg,k):
        pg.evaluate("k=>{S.view={x:cv.clientWidth/2,y:cv.clientHeight/2,k};applyView()}",k);pg.wait_for_timeout(120)
        return pg.evaluate("(()=>{const e=[...document.querySelectorAll('.lb')].find(x=>x.textContent=='소꿉친구');const r=e.getBoundingClientRect();return [r.height,parseFloat(getComputedStyle(e).fontSize)*S.view.k]})()")
    h1,h2,h07=lh(pg,1),lh(pg,2),lh(pg,.7)
    ok('8 관계선 글자는 확대하면 커지고 축소하면 작아지되 배율(2배·0.7배)만큼 그대로 따라가진 않음',h07[0]<h1[0]<h2[0] and h2[0]<1.6*h1[0] and h07[0]>.7*h1[0] and abs(h1[1]-13)<.1)
    pg.evaluate("window.__n=0;const o=ovq;ovq=()=>{__n++;o()}");pg.evaluate("S.view.k=1.5;applyView()");n1=pg.evaluate("__n");pg.evaluate("applyView();applyView()");n2=pg.evaluate("__n")
    ok('9 확대 배율이 바뀌면 겹침 검사를 다시 하고, 배율이 그대로면(화면 이동 등) 안 함',n1>=1 and n2==n1)
    M=b.new_context(viewport={'width':500,'height':800}).new_page();M.goto(URL);M.wait_for_timeout(700);M.evaluate('alpha=0')
    mh=lh(M,1)
    ok('10 좁은 화면(500px)에선 관계선 글자가 1.15배쯤 더 큼',mh[0]>h1[0]*1.1)
    print('errors:',errs);b.close()
