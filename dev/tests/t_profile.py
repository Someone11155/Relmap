from helpers import *
import base64
# 창 위 마우스 휠 스크롤 + 인물 사진 버전(시청별) + 읽기 모드 프로필 모달 + 육각형 스탯
BASE='http://localhost:8765/index.html'
EDIT=BASE+'?mode=edit'
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
IA='data:image/png;base64,AAAA';IB='data:image/png;base64,BBBB'
# 작품 3개(영화1·영화2·드라마1 3화) + b·c·d·선·글자에 태그
SETUP="""()=>{const w=(id,title,kind,n)=>({id,t:'w',x:0,y:0,title,kind,ord:Date.now(),...(kind=='s'?{n}:{})});
 S.nodes.push(w('m1','영화1','m'),w('m2','영화2','m'),w('s1','드라마1','s',3));
 nd('b').tg=['m1'];nd('c').tg=['s1_1'];nd('d').tg=['s1_3'];lk('l2').tg=['m1'];sv()}"""
bg=lambda pg,i='b':pg.evaluate("i=>document.querySelector('.n.p[data-id=\"'+i+'\"] .im').style.backgroundImage",i)
pfv=lambda pg:pg.evaluate("!document.querySelector('#pf').hidden")
P=lambda i:f'.n.p[data-id="{i}"] .im'
def mk(b,w=1280,h=760,touch=False):
    c=b.new_context(viewport={'width':w,'height':h},has_touch=touch,is_mobile=touch) if touch else b.new_context(viewport={'width':w,'height':h})
    pg=c.new_page();pg.on('pageerror',lambda e:ERR.append(str(e)));pg.on('dialog',lambda d:(ERR.append('DIALOG:'+d.message),d.accept()));return pg
def tap(pg,sel):   # 터치 한 번 (눌렀다 떼기)
    bb=pg.locator(sel).bounding_box();x,y=bb['x']+bb['width']/2,bb['y']+bb['height']/2
    c=pg.context.new_cdp_session(pg);c.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});c.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
with sync_playwright() as p:
    b=p.chromium.launch();pg=mk(b)
    pg.goto(EDIT);settle(pg,700)
    # ── 1. 스크롤되는 창에서 마우스 휠
    pg.evaluate("for(let i=0;i<40;i++)S.nodes.push({id:'w'+i,t:'w',x:0,y:0,title:'작품'+i,kind:'m',ord:i});sv()")
    pg.click('#bw');settle(pg,300);k0=pg.evaluate('S.view.k');bb=pg.locator('#wk').bounding_box()
    pg.mouse.move(bb['x']+150,bb['y']+120);pg.mouse.wheel(0,400);settle(pg,300)
    ok('W1 작품 창 위에서 휠을 굴리면 창이 스크롤되고 화면은 확대되지 않음',pg.evaluate("wk.scrollHeight>wk.clientHeight&&wk.scrollTop>0")and pg.evaluate('S.view.k')==k0)
    pg.click('[data-wa=x]');pg.evaluate("select('b')");settle(pg,300);bb=pg.locator('#ins').bounding_box()
    pg.mouse.move(bb['x']+120,bb['y']+120);pg.mouse.wheel(0,300);settle(pg,300)
    ok('W2 인물 패널 위에서도 휠로 스크롤됨(확대 안 됨)',pg.evaluate("ins.scrollHeight>ins.clientHeight&&ins.scrollTop>0")and pg.evaluate('S.view.k')==k0)
    pg.evaluate("select(null)");pg.mouse.move(640,700);pg.mouse.wheel(0,-300);settle(pg,300)
    ok('W3 빈 화면 위에서는 예전처럼 휠로 확대됨',pg.evaluate('S.view.k')>k0)
    pg.evaluate("S.nodes=S.nodes.filter(n=>!/^w\\d+$/.test(n.id));sv()")
    # ── 2. 인물 사진 버전
    pg.evaluate(SETUP);pg.evaluate("select('b')");settle(pg,300)
    ok('P1 인물 패널에 「시청에 따라 바뀌는 사진」 추가 버튼이 있음',pg.locator('#ins [data-a=ima]').count()==1 and '시청에 따라 바뀌는 사진' in pg.inner_text('#ins'))
    f=tempfile.mktemp(suffix='.png');open(f,'wb').write(PNG)
    with pg.expect_file_chooser() as fc: pg.click('#ins [data-a=ima]')
    fc.value.set_files(f);settle(pg,800)
    ok('P2 사진을 첨부하면 JPEG 로 저장되고 작품 선택 칸이 생김',pg.evaluate("nd('b').im.length==1&&nd('b').im[0].img.startsWith('data:image/jpeg')&&nd('b').im[0].g==''")and pg.locator('#ins [data-ig="0"]').count()==1)
    pg.select_option('#ins [data-ig="0"]','m1');settle(pg,200)
    ok('P3 이 작품을 본 뒤에 바뀌는 사진: 영화·에피소드 이름으로 고르면 저장됨',pg.evaluate("nd('b').im[0].g")=='m1' and '드라마1 3화' in pg.inner_text('#ins [data-ig="0"]'))
    pg.evaluate("nd('b').im=[{img:'%s',g:'m1'},{img:'%s',g:'m2'}];upd(nd('b'));sv()"%(IA,IB));settle(pg,200)
    ok('P4 편집 모드에서는 기본 사진만 보임(여기선 사진 없음)',bg(pg)=='none')
    pg.click('#bm');settle(pg,300)
    ok('P5 읽기 모드: 아직 아무것도 안 봤으면 기본 사진',bg(pg)=='none')
    pg.evaluate("WS.add('m1');drawLinks()");settle(pg,200);a=bg(pg)
    pg.evaluate("WS.add('m2');drawLinks()");settle(pg,200);c2=bg(pg)
    pg.evaluate("WS.delete('m1');drawLinks()");settle(pg,200);d2=bg(pg)
    ok('P6 본 작품에 맞는 사진으로 바뀌고, 여러 개를 봤으면 아래쪽 사진이 우선',('AAAA' in a)and('BBBB' in c2)and('BBBB' in d2))
    pg.evaluate("WS.clear();drawLinks()");settle(pg,200)
    r=pg.evaluate("cleanEnt('n',{t:'p',im:[{img:'javascript:x',g:'ok'},{img:'%s',g:'bad id!'},null,...Array(20).fill({img:'%s',g:'m1'})]}).im"%(IA,IA))
    ok('P7 불러온 파일의 이상한 사진 값은 걸러짐(주소 형식·작품 id·12개까지)',len(r)==12 and r[0]=={'img':'','g':'ok'} and r[1]=={'img':IA,'g':''} and r[2]=={'img':'','g':''})
    # ── 3. 읽기 모드 프로필 모달
    pg.evaluate("nd('b').im=[];nd('b').img='';upd(nd('b'))")
    R_=mk(b);R_.goto(BASE);settle(R_,800)
    ok('M0 읽기 모드로 시작',R_.evaluate('cv.dataset.mode')=='r' and not pfv(R_))
    R_.click(P('b'));settle(R_,400);t=R_.inner_text('#pf')
    ok('M1 인물을 누르면 프로필 모달이 뜸(이름·설명 표시, 예전 패널은 안 뜸)',pfv(R_) and '김서준' in t and '주인공' in t and R_.eval_on_selector('#ins','e=>getComputedStyle(e).display')=='none')
    ok('M2 모달에 연결된 인물(관계 이름)과 소속 그룹이 보임',R_.locator('#pf .go').count()==2 and '소꿉친구' in t and '라이벌' in t and R_.locator('#pf .gr').count()==1 and '문예부' in t)
    R_.click('#pf .go >> text=이하린');settle(R_,300)
    ok('M3 연결된 인물을 누르면 그 인물의 프로필로 바뀜',R_.inner_text('#pf .pf-n')=='이하린' and R_.locator('#pf .go').count()==1)
    R_.keyboard.press('Escape');settle(R_,200)
    ok('M4 Esc 로 닫히고 인물 선택도 풀림',not pfv(R_) and R_.evaluate("sel===null&&!cv.inert"))
    R_.click(P('b'));settle(R_,500);R_.click('#pf [data-pf=x]');settle(R_,200);c1=not pfv(R_)
    R_.click(P('b'));settle(R_,500);R_.click('.pf-scrim',position={'x':5,'y':5});settle(R_,200)
    ok('M5 닫기 버튼과 바깥(어두운 곳) 누르기로도 닫힘',c1 and not pfv(R_))
    bb=R_.locator(P('b')).bounding_box();x,y=bb['x']+bb['width']/2,bb['y']+bb['height']/2
    R_.mouse.move(x,y);R_.mouse.down();R_.mouse.move(x+80,y+40,steps=8);R_.mouse.up();settle(R_,500)
    ok('M6 인물을 끌었다 놓으면 프로필 모달이 안 뜸',not pfv(R_))
    R_.click(P('b'));settle(R_,500);bb=R_.locator('#pf .pf-card').bounding_box()
    ok('M7 모달이 화면 안에 들어오고 뒤쪽은 눌러지지 않음',pfv(R_) and bb['x']>=0 and bb['y']>=0 and bb['x']+bb['width']<=1280 and R_.evaluate("cv.inert"))
    R_.keyboard.press('Escape')
    T=mk(b,390,760,True);T.goto(BASE);settle(T,800);tap(T,P('b'));settle(T,900)
    ok('M8 모바일 터치로 짧게 누르면 모달이 뜨고 바로 닫히지 않음',pfv(T) and '김서준' in T.inner_text('#pf'))
    # 스포일러: 안 본 작품의 인물·관계·설명이 모달에 안 새는지
    S_=mk(b);S_.goto(EDIT);settle(S_,700);S_.evaluate(SETUP)
    S_.evaluate("nd('b').dx=[{t:'1부 비밀',g:'m1'},{t:'결말 반전',g:'s1_3'}];nd('b').st=['힘','지능','매력','민첩','체력','의지'].map(n=>({n,v:5}));sv()")
    S_.click('#bm');settle(S_,300);S_.evaluate("WS.add('m1');drawLinks()");settle(S_,200)
    S_.click(P('b'));settle(S_,500);t=S_.inner_text('#pf')
    ok('M9 안 본 작품의 인물·관계·추가 설명은 모달에 안 나옴',pfv(S_) and '1부 비밀' in t and '결말 반전' not in t and S_.locator('#pf .go').count()==0 and '이하린' not in t and '박도윤' not in t and '인물 1명' in t)
    S_.evaluate("WS.add('s1_1');drawLinks();pfRender()");settle(S_,200)
    ok('M10 그 작품을 봤다고 체크하면 열려 있는 모달에도 반영됨',S_.locator('#pf .go').count()==1 and '이하린' in S_.inner_text('#pf'))
    S_.evaluate("nd('b').im=[{img:'%s',g:'m1'}];upd(nd('b'));drawLinks();pfRender()"%IB);settle(S_,200)
    ok('M11 모달의 큰 사진도 본 작품에 맞는 버전이 보임',IB in S_.get_attribute('#pf .pf-av img','src'))
    # ── 4. 육각형 스탯
    H=mk(b);H.goto(EDIT);settle(H,700);H.evaluate("select('b')");settle(H,300)
    ok('H1 인물 패널에 「육각형 스탯 추가」 버튼이 있고 처음엔 스탯이 없음',H.locator('#ins [data-a=sta]').count()==1 and H.evaluate("nd('b').st")is None)
    H.click('#ins [data-a=sta]');settle(H,300)
    ok('H2 추가하면 항목 6개(이름·값 5)가 생기고 육각형 그림이 보임',H.evaluate("nd('b').st.length==6&&nd('b').st.every(x=>x.v==5&&x.n)")and H.locator('#hxp svg.hx text.ht').count()==6 and H.locator('#ins [data-sn]').count()==6)
    H.fill('#ins [data-sn="0"]','민첩함이엄청나');H.eval_on_selector('#ins [data-sv="1"]',"e=>{e.value=9;e.dispatchEvent(new Event('input',{bubbles:true}))}");settle(H,300)
    ok('H3 이름(6글자까지)·값을 바꾸면 저장되고 그림·숫자가 바로 바뀜',H.evaluate("nd('b').st[0].n.length")<=6 and H.evaluate("nd('b').st[1].v")==9 and '9' in H.get_attribute('#hxp svg','aria-label') and H.inner_text('#ins [data-sv="1"] + span')=='9')
    H.click('#bm');settle(H,300);H.click(P('b'));settle(H,500)
    ok('H4 읽기 모드 프로필 모달에 육각형 스탯이 보임(항목 이름·값)',H.locator('#pf svg.hx polygon').count()==6 and '9' in H.get_attribute('#pf svg.hx','aria-label'))
    H.keyboard.press('Escape');H.click(P('c'));settle(H,500)
    ok('H5 스탯이 없는 인물의 모달에는 그림이 없음',H.locator('#pf svg.hx').count()==0)
    H.keyboard.press('Escape');H.click('#bm');settle(H,300);H.evaluate("select('b')");settle(H,300);H.click('#ins [data-a=std]');settle(H,200)
    ok('H6 스탯 삭제 버튼: 스탯이 지워지고 추가 버튼이 다시 보임',H.evaluate("nd('b').st")is None and H.locator('#ins [data-a=sta]').count()==1)
    r=H.evaluate("({a:cleanEnt('n',{t:'p',st:[1,2]}).st,b:cleanEnt('n',{t:'p',st:[{n:'가나다라마바사',v:99},{n:5,v:-4},{v:'x'},null,{n:'e',v:3.6},{n:'f',v:2}]}).st})")
    ok('H7 불러온 파일의 스탯 검증(3~12개가 아니면 버림, 값 0~10, 이름 6글자, 이상한 값은 0)',r['a'] is None and r['b']==[{'n':'가나다라마바','v':10},{'n':'','v':0},{'n':'','v':0},{'n':'','v':0},{'n':'e','v':4},{'n':'f','v':2}])
    # ── 방 안: 사진 버전·스탯이 서로 동기화됨
    A=client(b,"");B=client(b,"")
    A.goto(EDIT);settle(A,500);A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    B.goto(BASE+h);settle(B,1800)
    A.evaluate(SETUP);A.evaluate("nd('b').im=[{img:'%s',g:'m1'}];nd('b').st=['a','b','c','d','e','f'].map(n=>({n,v:7}));sv()"%IA);settle(A,1800)
    ok('R1 방: A 가 쓴 사진 버전·스탯이 B 와 DB 에 똑같이 반영됨',same(A,B,room=room) and B.evaluate("nd('b').im[0].g=='m1'&&nd('b').st[0].v==7"))
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    b.close()
