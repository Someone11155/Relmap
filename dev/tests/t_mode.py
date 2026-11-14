from helpers import *
# 읽기/편집/이동 모드 + 드래그 중 프로필 패널이 뜨지 않는지(마우스·터치) 검증
BASE='http://localhost:8765/index.html'      # 모드 지정 없음 = 읽기 모드로 시작
EDIT=BASE+'?mode=edit'
vis=lambda pg:pg.eval_on_selector('#ins','e=>getComputedStyle(e).display')!='none'
mode=lambda pg:pg.evaluate("cv.dataset.mode")
pos=lambda pg,i:pg.evaluate("i=>{const n=nd(i);return [Math.round(n.x),Math.round(n.y)]}",i)
view=lambda pg:pg.evaluate("[Math.round(S.view.x),Math.round(S.view.y),+S.view.k.toFixed(3)]")
def ctr(pg,sel):
    bb=pg.locator(sel).bounding_box();return bb['x']+bb['width']/2,bb['y']+bb['height']/2
def mdrag(pg,sel,dx,dy,btn='left',steps=8):
    x,y=ctr(pg,sel);pg.mouse.move(x,y);pg.mouse.down(button=btn);pg.mouse.move(x+dx,y+dy,steps=steps);pg.mouse.up(button=btn);pg.wait_for_timeout(150)
def touch(pg,x,y,dx,dy,n=8,mid=None):
    c=pg.context.new_cdp_session(pg);S_=lambda t,pts:c.send('Input.dispatchTouchEvent',{'type':t,'touchPoints':pts})
    S_('touchStart',[{'x':x,'y':y}])
    for i in range(1,n+1):
        S_('touchMove',[{'x':x+dx*i/n,'y':y+dy*i/n}])
        if mid and i==n//2:mid()
    r=vis(pg);S_('touchEnd',[]);pg.wait_for_timeout(200);return r
P='.n.p[data-id="b"] .im'
with sync_playwright() as p:
    b=p.chromium.launch()
    # ── 방 안에서 드래그하는 동안 남의 변경이 도착해도 프로필 패널이 뜨지 않아야 함
    A=client(b,"");B=client(b,"")
    A.goto(EDIT);settle(A,500);A.click('#bk');settle(A,1500);h=A.evaluate('location.hash')
    B.goto(EDIT+h);settle(B,1800)
    x,y=ctr(A,P);A.mouse.move(x,y);A.mouse.down();A.mouse.move(x+30,y+10,steps=6)
    mdrag(B,'.n.p[data-id="c"] .im',40,40);settle(A,700)   # 드래그 중인 A 쪽으로 B 의 변경이 도착
    A.mouse.move(x+60,y+20,steps=6);settle(A,400)
    ok('T1 방 안 드래그 중 남의 변경이 와도 프로필 패널이 안 뜸',not vis(A))
    A.mouse.up();settle(A,500)
    ok('T2 드래그를 놓은 뒤에도 패널이 안 뜸(움직였으므로)',not vis(A))
    A.mouse.click(x+60,y+20);settle(A,500)
    ok('T3 그냥 클릭하면 패널이 뜸',vis(A))
    # ── 터치로 끌 때(혼자 쓰기): 끄는 동안 패널이 없고, 짧게 누르면 뜸
    ctx=b.new_context(viewport={'width':390,'height':760},has_touch=True,is_mobile=True);T=ctx.new_page();T.on('pageerror',lambda e:ERR.append(str(e)))
    T.goto(EDIT);settle(T,700);T.evaluate('alpha=0')
    x,y=ctr(T,P);mid=touch(T,x,y,60,30)
    ok('T4 터치로 인물을 끌 때 프로필 패널이 안 뜸',not mid and not vis(T))
    x,y=ctr(T,P);touch(T,x,y,0,0,n=1)
    ok('T5 터치로 짧게 누르면 패널이 뜸',vis(T))
    # ── 모드 (혼자 쓰기)
    ctx=b.new_context(viewport={'width':1280,'height':760});R_=ctx.new_page();R_.on('pageerror',lambda e:ERR.append(str(e)));R_.on('dialog',lambda d:(ERR.append('DIALOG:'+d.message),d.accept()))
    R_.goto(BASE);settle(R_,700)
    ok('M1 모드 지정 없이 열면 읽기 모드',mode(R_)=='r')
    ok('M2 읽기 모드에선 편집 도구가 안 보이고 보기·저장 도구는 보임',not R_.is_visible('[data-t=p]') and not R_.is_visible('#bun') and not R_.is_visible('#bv') and R_.is_visible('#bs') and R_.is_visible('#zi'))
    p0=pos(R_,'b');v0=view(R_);mdrag(R_,P,80,40)
    ok('M3 읽기: 인물을 끌어도 저장된 위치는 안 바뀜(화면에서만 탄성 있게 움직임)',pos(R_,'b')==p0)
    v0=view(R_);R_.mouse.move(60,650);R_.mouse.down();R_.mouse.move(160,600,steps=6);R_.mouse.up()
    ok('M3b 읽기: 빈 곳을 끌면 화면이 이동',view(R_)!=v0)
    ok('M4 읽기: 끈 뒤에 프로필이 안 뜸',not vis(R_))
    R_.click(P);settle(R_,200)
    ok('M5 읽기: 인물을 누르면 읽기 전용 프로필(입력칸 없음, 이름 표시)',vis(R_) and R_.locator('#ins input,#ins textarea').count()==0 and '김서준' in R_.inner_text('#ins'))
    mdrag(R_,P,40,40);settle(R_,100)
    ok('M6 읽기: 프로필이 열린 채 인물을 끌면 프로필이 닫힘',not vis(R_))
    n0=R_.evaluate('S.nodes.length');R_.click(P);R_.keyboard.press('Delete');R_.keyboard.press('KeyM');settle(R_,200)
    ok('M7 읽기: Delete 로 안 지워지고 M 키도 무시됨',R_.evaluate('S.nodes.length')==n0 and mode(R_)=='r')
    R_.click('#bm');settle(R_,200);R_.evaluate('alpha=0')
    ok('M8 편집 버튼 → 편집 모드(도구와 이동 버튼이 보임)',mode(R_)=='e' and R_.is_visible('[data-t=p]') and R_.is_visible('#bv'))
    n1=R_.evaluate('S.nodes.length');R_.click('[data-t=p]');settle(R_,200);added=R_.evaluate('S.nodes.length')==n1+1;R_.keyboard.press('Delete');settle(R_,100)   # 새 인물이 b 위에 겹쳐 남지 않게 바로 지움
    ok('M9 편집: 인물 추가가 됨',added)
    p0=pos(R_,'b');mdrag(R_,P,60,30);R_.evaluate('alpha=0')
    ok('M10 편집: 인물을 끌면 움직임',pos(R_,'b')!=p0)
    R_.keyboard.press('Escape');settle(R_,100)
    p0=pos(R_,'b');v0=view(R_);mdrag(R_,P,-90,50,btn='right')
    ok('M11 편집: 인물 위에서 우클릭 드래그하면 선택 없이 화면만 이동',pos(R_,'b')==p0 and view(R_)!=v0 and R_.evaluate('sel')is None and not vis(R_))
    R_.click(P);settle(R_,200);mdrag(R_,'.n.p[data-id="c"] .im',50,50,btn='right')
    ok('M12 편집: 우클릭 드래그해도 기존 선택·패널은 그대로',R_.evaluate('sel')=='b' and vis(R_))
    R_.keyboard.press('Escape');R_.keyboard.press('KeyM');settle(R_,200)
    ok('M13 M 키 → 이동 모드(같은 화면, 도구는 못 누름)',mode(R_)=='m' and R_.is_visible('[data-t=p]') and R_.evaluate("document.querySelector('[data-t=p]').inert") and R_.evaluate("document.querySelector('#bv').classList.contains('on')"))
    p0=pos(R_,'b');v0=view(R_);mdrag(R_,P,70,30)
    ok('M14 이동: 인물 위를 끌어도 화면만 이동(선택 없음)',pos(R_,'b')==p0 and view(R_)!=v0 and R_.evaluate('sel')is None)
    R_.click(P);settle(R_,200)
    ok('M15 이동: 인물을 눌러도 선택·프로필이 없음',R_.evaluate('sel')is None and not vis(R_))
    k0=view(R_)[2];R_.mouse.move(600,400);R_.mouse.wheel(0,-300);settle(R_,200)
    ok('M16 이동: 휠 확대·축소는 됨',view(R_)[2]>k0)
    R_.click('#bf');settle(R_,300);R_.click('#bv');settle(R_,100)
    ok('M17 이동 버튼으로 편집 상태로 돌아옴(도구 다시 사용 가능)',mode(R_)=='e' and not R_.evaluate("document.querySelector('[data-t=p]').inert"))
    R_.click(P);settle(R_,200);R_.click('#ins input[data-k=name]');R_.keyboard.press('KeyM');settle(R_,100)
    ok('M18 이름 입력 중 M 키는 모드를 바꾸지 않음',mode(R_)=='e')
    # ── 방 안: 읽기 모드는 남의 변경을 보여 주되 내 쪽에서는 바꿀 수 없음
    A=client(b,"");Bc=client(b,"")
    A.goto(EDIT);settle(A,500);A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    Bc.goto(BASE+h);settle(Bc,1800)
    ok('R1 방 링크로 열면 읽기 모드',mode(Bc)=='r')
    mdrag(A,P,60,30);settle(A,1500)
    ok('R2 읽기 모드 화면에도 남의 변경이 실시간으로 보임',pos(Bc,'b')==pos(A,'b') and same(A,Bc,room=room))
    pb=pos(Bc,'b');mdrag(Bc,P,-80,-40);settle(Bc,1500)
    ok('R3 읽기 모드에서 끌어도 방의 내용은 안 바뀜',pos(Bc,'b')==pb and same(A,Bc,room=room))
    dp=tempfile.mktemp(suffix='.json');json.dump({'nodes':[],'links':[]},open(dp,'w'))
    with Bc.expect_file_chooser() as fc:
        Bc.click('#bl')
    fc.value.set_files(dp);settle(Bc,1500)
    ok('R4 읽기 모드에선 방 전체를 파일로 덮어쓸 수 없음',Bc.evaluate('S.nodes.length')>0 and same(A,Bc,room=room))
    # ── 링크 공유: 「링크 복사」는 편집용·감상용 두 링크를 고르는 드롭다운
    A.evaluate("window.__cp=null;navigator.clipboard.writeText=async t=>{window.__cp=t}")
    A.click('#bk');settle(A,300)
    bk=A.locator('#bk').bounding_box();dd=A.locator('#dl').bounding_box()
    ok('S1 링크 복사를 누르면 버튼 바로 아래에 편집용·감상용 선택이 뜸',A.locator('#dl [data-da=le]').count()==1 and A.locator('#dl [data-da=lv]').count()==1 and abs(dd['y']-(bk['y']+bk['height']))<=20 and abs(dd['x']-bk['x'])<=60)
    A.click('#dl [data-da=lv]');settle(A,300);lv=A.evaluate('window.__cp')
    A.click('#dl [data-da=le]');settle(A,300);le=A.evaluate('window.__cp')
    ok('S2 링크는 방 주소에 m=r(감상)·m=e(편집)이 붙고 주소창은 그대로',lv and le and lv.endswith('#room='+room+'&m=r') and le.endswith('#room='+room+'&m=e') and A.evaluate('location.hash')=='#room='+room)
    A.click('#bk');settle(A,300)
    ok('S3 한 번 더 누르면 닫힘',A.evaluate("getComputedStyle(document.querySelector('#dl')).display")=='none')
    Cv=client(b,"");Ce=client(b,"")
    Cv.goto(lv.replace(lv.split('#')[0],BASE));settle(Cv,1800);Ce.goto(le.replace(le.split('#')[0],BASE));settle(Ce,1800)
    ok('S4 감상용 링크는 읽기 모드, 편집용 링크는 편집 모드로 열림',mode(Cv)=='r' and mode(Ce)=='e' and same(A,Cv,room=room))
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    b.close()
