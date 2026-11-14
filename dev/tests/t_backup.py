from helpers import *
import base64
# 6단계 자동 백업(보관·복원·초기화 직전 보관) + 7단계 그룹 원 배경 이미지(첨부·표시·검증·방 동기화)
BASE='http://localhost:8765/index.html'
EDIT=BASE+'?mode=edit'
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
bk=lambda pg:pg.evaluate("bkList().map(b=>[b.n,b.l])")
with sync_playwright() as p:
    b=p.chromium.launch();A=client(b,"")
    A.goto(EDIT);settle(A,700)
    ok('B1 열자마자 현재 모습이 자동 백업 1개로 보관됨',len(bk(A))==1 and bk(A)[0][0]==3)
    A.evaluate("nd('b').name='변경';bkSnap()")
    ok('B2 5분이 안 지나면 바뀌어도 새 백업을 만들지 않음',len(bk(A))==1)
    # ── 초기화 직전 보관 → 복원
    A.click('#br');A.click('#br');settle(A,400)
    ok('B3 초기화하면 바로 직전 모습이 백업에 추가됨',len(bk(A))==2 and A.evaluate('S.nodes.filter(n=>n.t!="w").length')==0)
    A.click('#bb');settle(A,300)
    bb=A.locator('#bb').bounding_box();dd=A.locator('#dl').bounding_box()
    ok('B4 백업 버튼 바로 아래에 시점 목록이 뜸(2개)',A.locator('#dl [data-da=rs]').count()==2 and abs(dd['y']-(bb['y']+bb['height']))<=20)
    A.click('#dl [data-da=rs][data-i="1"]');settle(A,600)
    ok('B5 예전 시점(처음 모습)으로 복원',A.evaluate("nd('b').name")=='김서준' and A.evaluate('S.nodes.filter(n=>n.t=="p").length')==3)
    A.click('#bb');settle(A,300);A.click('#bb');settle(A,300)
    ok('B6 백업 버튼을 한 번 더 누르면 목록이 닫힘',A.evaluate("getComputedStyle(document.querySelector('#dl')).display")=='none')
    A.reload();settle(A,700)
    ok('B7 새로고침해도 백업이 남아 있음',len(bk(A))>=2)
    # ── 그룹 원 배경 이미지
    gid=A.evaluate("add({t:'c',x:-300,y:-300,w:320,h:240,title:'G',col:'#0066FF',op:8,m:[],ph:true}).id");settle(A,300)
    ok('G1 그룹 패널에 배경 이미지 첨부 버튼이 있고 제거 버튼은 아직 없음',A.locator('#ins [data-a=img]').count()==1 and A.locator('#ins [data-a=rm]').count()==0)
    f=tempfile.mktemp(suffix='.png');open(f,'wb').write(PNG)
    with A.expect_file_chooser() as fc: A.click('#ins [data-a=img]')
    fc.value.set_files(f);settle(A,800)
    ok('G2 첨부하면 그룹에 JPEG 이미지가 저장되고 원 안에 40% 투명도 배경으로 보임',A.evaluate("g=>nd(g).img.startsWith('data:image/jpeg')&&(q=>q.backgroundImage.includes('url(')&&q.opacity=='0.4')(getComputedStyle(els[g],'::before'))",gid) and A.locator('#ins [data-a=rm]').count()==1)
    A.click('#ins [data-a=rm]');settle(A,300)
    ok('G3 제거하면 이미지가 없어짐',A.evaluate("g=>!nd(g).img&&!els[g].classList.contains('gi')",gid))
    ok('G4 잘못된 그림 값(스크립트·따옴표 섞임)은 걸러냄',A.evaluate("""()=>{const c=(i)=>cleanEnt('n',{t:'c',w:100,h:100,title:'x',col:'#000000',img:i});
      return c('data:image/png;base64,AAAA').img=='data:image/png;base64,AAAA'&&c('data:image/png;base64,AA");x:url(').img===undefined&&c('javascript:alert(1)').img===undefined&&cleanEnt('n',{t:'p',img:'data:image/png,a);b'}).img===''}"""))
    # ── 방 동기화
    B=client(b,"");A.evaluate("nd('%s').img='';upd(nd('%s'))"%(gid,gid))
    A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    B.goto(EDIT+h);settle(B,1800)
    with A.expect_file_chooser() as fc: A.evaluate("select('%s',true);panel()"%gid) or A.click('#ins [data-a=img]')
    fc.value.set_files(f);settle(A,2000)
    ok('G5 방 안에서 붙인 그룹 배경 이미지가 다른 사람 화면·서버에도 반영됨',B.evaluate("g=>(nd(g)||{}).img||''",gid).startswith('data:image/jpeg') and same(A,B,room=room))
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    b.close()
