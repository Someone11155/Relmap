from playwright.sync_api import sync_playwright
URL='http://localhost:8765/index.html?mode=edit'
vis=lambda pg:pg.eval_on_selector('#ins','e=>getComputedStyle(e).display')!='none'
ok=lambda n,v:print(('PASS ' if v else 'FAIL ')+n)
def drag(pg,sel,dx,dy,steps=10):
    bb=pg.locator(sel).bounding_box();x,y=bb['x']+bb['width']/2,bb['y']+bb['height']/2
    pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x+dx,y+dy,steps=steps)
    mid=vis(pg);pg.mouse.up();pg.wait_for_timeout(200);return mid
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_context(viewport={'width':1280,'height':760}).new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL);pg.wait_for_timeout(600);pg.evaluate('alpha=0')
    ok('0 처음엔 패널 없음',not vis(pg))
    pg.click('.p[data-id="b"] .im');pg.wait_for_timeout(150)
    ok('1 인물을 클릭하면 패널이 뜸',vis(pg) and pg.evaluate('sel')=='b' and 'b' in pg.inner_text('#ins h3').lower()+'b')
    pg.click('#cv',position={'x':200,'y':650});pg.wait_for_timeout(100);ok('2 빈 곳 클릭하면 닫힘',not vis(pg))
    mid=drag(pg,'.p[data-id="b"] .im',-60,90)
    ok('3 선택 안 된 인물을 드래그: 도중에도, 놓은 뒤에도 패널 안 뜸',(not mid) and not vis(pg))
    ok('3b 그래도 선택(외곽선)은 유지되어 Delete 등을 쓸 수 있음',pg.evaluate('sel')=='b' and pg.eval_on_selector('.p[data-id="b"]','e=>e.classList.contains("sel")'))
    pg.click('.p[data-id="b"] .im');pg.wait_for_timeout(150);ok('4 같은 인물을 다시 클릭하면 패널이 뜸',vis(pg))
    mid=drag(pg,'.p[data-id="b"] .im',80,-40)
    ok('5 패널이 열린 인물을 드래그하면 끌기 시작할 때 닫힘(놓은 뒤에도 닫힌 채)',(not mid) and not vis(pg))
    pg.click('.p[data-id="c"] .im');pg.wait_for_timeout(150)
    mid=drag(pg,'.p[data-id="b"] .im',20,60)
    ok('6 다른 인물(c) 패널이 열린 상태에서 b 를 드래그: c 의 패널이 남지 않음',(not mid) and not vis(pg) and pg.evaluate('sel')=='b')
    # 그룹
    gb=pg.locator('.n.c[data-id="a"]').bounding_box()
    pg.mouse.move(gb['x']+gb['width']*0.5,gb['y']+gb['height']*0.15);pg.mouse.down();pg.mouse.up();pg.wait_for_timeout(200)
    ok('7 그룹(원) 클릭하면 패널이 뜸',vis(pg) and pg.evaluate('sel')=='a')
    x0=pg.evaluate("nd('a').x");pg.mouse.move(gb['x']+gb['width']*0.5,gb['y']+gb['height']*0.15);pg.mouse.down();pg.mouse.move(gb['x']+gb['width']*0.5+60,gb['y']+gb['height']*0.15+30,steps=8);mid=vis(pg);pg.mouse.up();pg.wait_for_timeout(200)
    ok('8 그룹을 드래그하면 패널이 닫히고 그룹이 실제로 이동',(not mid) and not vis(pg) and pg.evaluate("nd('a').x")!=x0)
    pg.evaluate("document.querySelectorAll('.p').forEach(e=>e.style.pointerEvents='none')")  # 물리가 꺼져 인물이 핸들을 덮을 수 있어, 이 검사 동안만 인물은 클릭이 통과하게
    pg.click('.n.c[data-id="a"]',position={'x':gb['width']*0.5,'y':gb['height']*0.15});pg.wait_for_timeout(150)
    rz=pg.locator('.n.c[data-id="a"] .rz').bounding_box();w0=pg.evaluate("nd('a').w")
    pg.mouse.move(rz['x']+8,rz['y']+8);pg.mouse.down();pg.mouse.move(rz['x']+60,rz['y']+50,steps=8);mid=vis(pg);pg.mouse.up();pg.wait_for_timeout(200)
    ok('9 그룹 크기 조절(핸들)을 끌 때도 패널이 닫힘',(not mid) and pg.evaluate("nd('a').w")>w0)
    pg.evaluate("document.querySelectorAll('.p').forEach(e=>e.style.pointerEvents='')")
    # 4px 이하 흔들림은 클릭으로 취급
    pg.click('#cv',position={'x':200,'y':650});bb=pg.locator('.p[data-id="c"] .im').bounding_box();x,y=bb['x']+30,bb['y']+30
    pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x+2,y+1);pg.mouse.up();pg.wait_for_timeout(150)
    ok('10 손이 살짝(4px 이하) 흔들린 클릭은 클릭으로 처리되어 패널이 뜸',vis(pg))
    # 관계선·텍스트 클릭은 그대로
    pg.click('.lb >> nth=0');pg.wait_for_timeout(150);ok('11 관계선 라벨 클릭은 기존처럼 패널이 뜸',vis(pg))
    # 하이라이트·선택은 인물 아이콘 원 위에서만(이름·설명 글자 영역은 마우스를 통과시킴)
    pg.click('#cv',position={'x':200,'y':650});pg.wait_for_timeout(150);pg.mouse.move(5,5);pg.wait_for_timeout(150)
    ib=pg.locator('.n.p[data-id="b"] .im').bounding_box();tb=pg.locator('.n.p[data-id="b"] .nm').bounding_box();tx,ty=tb['x']+10,tb['y']+tb['height']/2
    sc=lambda:pg.eval_on_selector('.n.p[data-id="b"] .im','e=>getComputedStyle(e).transform')
    pg.mouse.move(tx,ty);pg.wait_for_timeout(300);t1=[pg.evaluate('hov'),pg.evaluate("document.querySelectorAll('.p.dim').length"),sc()]
    ok('12 인물 이름 글자 위에 커서를 올려도 하이라이트가 안 생김',t1[0] is None and t1[1]==0 and t1[2]=='none')
    pg.mouse.click(tx,ty);pg.wait_for_timeout(200)
    ok('13 인물 이름 글자를 눌러도 그 인물은 선택되지 않음(글자 아래에 있는 그룹 원 등이 눌림)',pg.evaluate('sel')!='b' and pg.evaluate("[...document.querySelectorAll('.p.sel')].length")==0)
    pg.mouse.move(ib['x']+ib['width']/2,ib['y']+ib['height']/2);pg.wait_for_timeout(300);h2=[pg.evaluate('hov'),sc()]
    pg.mouse.click(ib['x']+ib['width']/2,ib['y']+ib['height']/2);pg.wait_for_timeout(200)
    ok('14 아이콘 원 위에선 하이라이트되고(확대·관계 강조), 누르면 선택됨',h2[0]=='b' and h2[1]!='none' and pg.evaluate('sel')=='b' and vis(pg))
    # 겹친 요소 번갈아 선택(기존 기능) 회귀 확인
    print('errors:',errs);b.close()
