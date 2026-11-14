from helpers import *
# 에피소드 이름 + 읽기 모드 '본 작품' 선택과 안 본 작품(인물·선·그룹) 숨김
BASE='http://localhost:8765/index.html'
EDIT=BASE+'?mode=edit'
SETUP="""()=>{const w=(id,title,kind,n,en)=>({id,t:'w',x:0,y:0,title,kind,ord:Date.now(),...(kind=='s'?{n,en}:{})});
 S.nodes.push(w('m1','영화1','m'),w('m2','영화2','m'),w('s1','드라마1','s',3,['첫만남','','결말']));
 nd('b').tg=['m1'];nd('c').tg=['s1_1','s1_2'];nd('d').tg=['s1_3'];lk('l2').tg=['m1'];sv()}"""
shown=lambda pg,i:pg.evaluate("i=>els[i].style.display!='none'",i)
nlink=lambda pg:pg.evaluate("svg.querySelectorAll('line[data-id]').length")
P=lambda i:f'.n.p[data-id="{i}"] .im'
def mk(b):
    pg=b.new_context(viewport={'width':1280,'height':760}).new_page();pg.on('pageerror',lambda e:ERR.append(str(e)));pg.on('dialog',lambda d:(ERR.append('DIALOG:'+d.message),d.accept()));return pg
with sync_playwright() as p:
    b=p.chromium.launch();pg=mk(b)
    pg.goto(EDIT);settle(pg,700);pg.evaluate(SETUP);settle(pg,500)
    ok('V0 편집 모드에는 본 작품 버튼이 없고 전부 보임',not pg.is_visible('#bq') and all(shown(pg,i) for i in 'bcdae') and nlink(pg)==2)
    pg.click('#bm');settle(pg,300)
    ok('V1 읽기 모드 처음(아무것도 안 봄): 태그 있는 인물·그 선·멤버가 전부 숨은 그룹은 안 보이고, 글자 상자는 보임',pg.is_visible('#bq') and not any(shown(pg,i) for i in 'bcda') and shown(pg,'e') and nlink(pg)==0)
    pg.click('#bq');settle(pg,200)
    ok('V2 본 작품 창에 작품 3개(영화 2, 드라마 1)',pg.locator('#wk [data-ww], #wk [data-wwp]').count()==3 and '내가 본 작품' in pg.inner_text('#wk'))
    pg.check('[data-ww=m1]');settle(pg,200)
    ok('V3 영화1을 봤다고 체크: b 와 b 가 속한 그룹이 나타나고, c·d 와 선은 아직 숨김',shown(pg,'b') and shown(pg,'a') and not shown(pg,'c') and not shown(pg,'d') and nlink(pg)==0)
    pg.click('[data-wwx=s1]');settle(pg,100)
    txt=pg.inner_text('#wk')
    ok('V4 드라마 이름을 누르면 에피소드가 펼쳐지고 이름이 붙은 회차는 이름으로 보임',pg.locator('#wk .eps input').count()==3 and '첫만남' in txt and '2화' in txt and '결말' in txt)
    pg.check('[data-ww="s1_1"]');settle(pg,200)
    ok('V5 1화를 봤다고 체크: c 가 나타나고 b–c 선(태그 없음)이 보임, d 는 숨김',shown(pg,'c') and not shown(pg,'d') and nlink(pg)==1 and pg.evaluate("document.querySelector('[data-wwp]').indeterminate"))
    pg.click('[data-wwp=s1]');settle(pg,200)
    ok('V6 드라마 체크박스를 누르면 모든 에피소드를 본 것으로 처리: d·선 모두 보임',shown(pg,'d') and nlink(pg)==2 and pg.locator('#wk .eps input:checked').count()==3)
    pg.click('[data-wa=none]');settle(pg,200)
    ok('V7 모두 해제하면 다시 전부 숨김',not any(shown(pg,i) for i in 'bcd') and nlink(pg)==0)
    pg.click('[data-wa=all]');settle(pg,200)
    ok('V8 모두 봤어요를 누르면 전부 보임',all(shown(pg,i) for i in 'bcdae') and nlink(pg)==2)
    pg.click('[data-wa=none]');pg.check('[data-ww=m1]');pg.click('[data-wa=x]');settle(pg,200)
    pg.click(P('b'));settle(pg,300);t=pg.inner_text('#ins')
    ok('V9 프로필에 안 본 작품·숨은 인물과의 관계가 새지 않음(영화1만 표시, 연결 목록 없음)',pg.is_visible('#ins') and '등장: 영화1' in t and '영화2' not in t and '드라마' not in t and pg.locator('#ins .go').count()==0)
    pg.click('#bq');pg.check('[data-ww="s1_1"]')  # 드라마는 V4 에서 이미 펼쳐 둔 상태;pg.click('[data-wa=x]');settle(pg,200)
    pg.click(P('b'));settle(pg,300)
    ok('V10 c 를 보게 되면 b 의 프로필에 c 와의 관계가 나타남',pg.locator('#ins .go').count()==1)
    pg.goto(BASE);settle(pg,900)
    ok('V11 새로고침해도 본 작품이 유지됨(이 브라우저에 저장)',pg.evaluate("cv.dataset.mode")=='r' and shown(pg,'b') and shown(pg,'c') and not shown(pg,'d') and 'relmap_watch_local' in pg.evaluate("Object.keys(localStorage).join()"))
    pg.click('#bm');settle(pg,300)
    ok('V12 편집 모드로 가면 안 본 것도 전부 보임',all(shown(pg,i) for i in 'bcdae') and nlink(pg)==2 and pg.evaluate("HID.size")==0)
    # ── 에피소드 이름 (편집)
    pg.click('#bw');pg.click('[data-wex=s1]');settle(pg,100)
    ok('V13 에피소드 이름 입력칸(번호가 안내 글자, 이미 붙인 이름이 채워짐)',pg.locator('#wk [data-we]').count()==3 and pg.get_attribute('#wk [data-we][data-i="1"]','placeholder')=='2화' and pg.input_value('#wk [data-we][data-i="0"]')=='첫만남')
    pg.fill('#wk [data-we][data-i="1"]','둘째');settle(pg,200)
    ok('V14 이름을 쓰면 작품 데이터에 저장됨',pg.evaluate("nd('s1').en")==['첫만남','둘째','결말'])
    pg.click('[data-wa=x]');pg.evaluate("select('c')");settle(pg,100);pg.click('[data-tgx="s1"]');settle(pg,100)
    ok('V15 인물 패널의 에피소드 체크 목록에도 이름이 보임',all(x in pg.inner_text('#ins .eps') for x in ['첫만남','둘째','결말']))
    pg.click('#bw');pg.click('[data-wex=s1]') if not pg.is_visible('#wk [data-we]') else None
    pg.locator('[data-wn]').fill('2');pg.keyboard.press('Tab');settle(pg,200)
    ok('V16 에피소드 수를 줄이면 남는 이름만 유지',pg.evaluate("nd('s1').en")==['첫만남','둘째'])
    r=pg.evaluate("cleanDoc({nodes:[{id:'w1',t:'w',kind:'s',n:3,en:['x'.repeat(300),5,'ok','extra']}],links:[]}).nodes[0].en")
    ok('V17 불러온 파일의 이상한 에피소드 이름은 걸러짐(길이 100, 글자 아닌 값은 빈칸, 수 초과분 삭제)',r==['x'*100,'','ok'])
    # ── 방 안: 편집 쪽은 전부 보이고, 읽기 쪽은 각자 본 작품에 따라 숨김
    A=client(b,"");B=client(b,"")
    A.goto(EDIT);settle(A,500);A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    B.goto(BASE+h);settle(B,1800)
    A.evaluate(SETUP);settle(A,1800)
    ok('R1 방: 편집 쪽(A)은 전부 보이고 읽기 쪽(B)은 태그 있는 인물이 숨음',all(shown(A,i) for i in 'bcd') and not any(shown(B,i) for i in 'bcd') and same(A,B,room=room))
    B.click('#bq');B.check('[data-ww=m1]');settle(B,300)
    ok('R2 B 가 영화1을 봤다고 체크하면 B 화면에서만 b 가 나타나고 방 데이터는 그대로',shown(B,'b') and not shown(B,'c') and all(shown(A,i) for i in 'bcd') and same(A,B,room=room) and ('relmap_watch_'+room) in B.evaluate("Object.keys(localStorage).join()"))
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    b.close()
