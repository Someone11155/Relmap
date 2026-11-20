# 사진 서버(R2): 방 안에서 붙인 사진은 서버(Worker→R2)에 올라가 주소만 문서에 들어감 / 혼자 쓸 땐 예전처럼 / 올리기 실패 / 주소 검증 / 옮기기 버튼 / 파일 저장 시 사진 포함
# 가짜 R2 는 dev/fakesb.mjs 가 진짜 Worker 코드(../worker/photos.mjs)를 8791 포트에 올려서 흉내냄
import base64, tempfile, json, urllib.request
from playwright.sync_api import sync_playwright
from helpers import *
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
PH='http://localhost:8791'; PRE="localStorage.setItem('relmap_photo','%s');"%PH
r2=lambda:api('/r2stat')
def put(pg,data,token='fk_x'):   # 페이지 안에서 Worker 에 직접 PUT → (상태, 본문)
    return pg.evaluate("""async([d,t])=>{const r=await fetch('%s/',{method:'PUT',headers:{authorization:t?'Bearer '+t:'','content-type':'image/jpeg'},body:new Uint8Array(d)});return[r.status,await r.text()]}"""%PH,[list(data),token])
with sync_playwright() as p:
    b=p.chromium.launch();A=client(b,PRE);B=client(b,PRE);S=client(b,PRE)
    f=tempfile.mktemp(suffix='.png');open(f,'wb').write(PNG)
    # ── 혼자 쓸 땐(방 밖) 예전처럼 문서 안에 data URL
    S.goto(URL);settle(S,500);gs=S.evaluate("add({t:'c',x:-300,y:-300,w:320,h:240,title:'G',col:'#0066FF',op:8,m:[],ph:true}).id");settle(S,300)
    with S.expect_file_chooser() as fc: S.click('#ins [data-a=img]')
    fc.value.set_files(f);settle(S,800)
    ok('P1 혼자 쓸 땐 사진을 서버에 안 올리고 문서 안(data URL)에 넣음',S.evaluate("g=>nd(g).img.startsWith('data:image/jpeg')",gs) and r2()['count']==0)
    # ── 방 안: 올라가고 주소만 문서에 들어감
    A.goto(URL);settle(A,500);A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    B.goto(URL+h);settle(B,1800)
    gid=A.evaluate("add({t:'c',x:-300,y:-300,w:320,h:240,title:'G',col:'#0066FF',op:8,m:[],ph:true}).id");settle(A,500)
    with A.expect_file_chooser() as fc: A.click('#ins [data-a=img]')
    fc.value.set_files(f);settle(A,2500)
    u=A.evaluate("g=>nd(g).img",gid)
    ok('P2 방 안에서 붙이면 문서에는 서버 주소(해시.jpg)만 들어감',u.startswith(PH+'/') and len(u)==len(PH)+1+64+4 and r2()['count']==1)
    row=[x for x in api('/dump?room='+room)['data'] if x['id']==gid][0]
    ok('P3 서버 DB 행에는 사진 내용이 없어 작음(%d바이트)'%len(json.dumps(row)),'base64' not in json.dumps(row) and len(json.dumps(row))<600)
    ok('P4 다른 사람 화면에도 같은 주소로 보이고 실제로 받아짐',B.evaluate("g=>nd(g).img",gid)==u and B.evaluate("async u=>{const r=await fetch(u);return r.ok&&r.headers.get('content-type')=='image/jpeg'&&r.headers.get('cache-control').includes('immutable')}",u))
    # 같은 사진을 또 올려도 서버에는 한 장
    g3=A.evaluate("add({t:'c',x:-300,y:300,w:200,h:200,title:'I',col:'#0066FF',op:8,m:[],ph:true}).id");settle(A,500)
    with A.expect_file_chooser() as fc: A.click('#ins [data-a=img]')
    fc.value.set_files(f);settle(A,2500)
    ok('P5 같은 사진은 같은 주소·서버에 한 번만 저장됨',A.evaluate("g=>nd(g).img",g3)==u and r2()['count']==1)
    pi=A.evaluate("S.nodes.find(o=>o.t=='p').id")
    # ── 서버가 거부하는 경우
    ok('P6 로그인 토큰이 없으면 401',put(A,b'\xff\xd8\xff\xe0'+b'x'*50,token='')[0]==401)
    ok('P7 JPEG 가 아니면 415·너무 크면 413',put(A,PNG)[0]==415 and put(A,b'\xff\xd8\xff'+b'x'*310000)[0]==413)
    # ── 올리기 실패(서버가 안 열림)면 사진을 붙이지 않고 알림, 문서에 data URL 로 몰래 넣지 않음
    g2=A.evaluate("add({t:'c',x:300,y:-300,w:200,h:200,title:'H',col:'#0066FF',op:8,m:[],ph:true}).id");settle(A,500)
    A.route('**/localhost:8791/**',lambda r:r.abort())
    with A.expect_file_chooser() as fc: A.click('#ins [data-a=img]')
    fc.value.set_files(f);settle(A,900)
    ok('P8 올리기에 실패하면 사진이 붙지 않고 data URL 도 안 들어감',A.evaluate("g=>!nd(g).img",g2) and A.evaluate("document.querySelector('#bk .bt').textContent").startswith('사진을 올리지'))
    A.unroute('**/localhost:8791/**')
    # ── 주소 검증: 이 서버의 해시.jpg 만 통과(남이 넣은 외부 주소로 보는 사람 브라우저가 요청하는 것을 막음)
    ok('P9 이 서버 주소·data URL 은 통과, 외부 주소·이상한 경로는 거름',A.evaluate("""()=>{const h='a'.repeat(64),c=i=>cleanEnt('n',{t:'p',img:i,im:[{img:i,g:''}]}).img;
      return c('%s/'+h+'.jpg')=='%s/'+h+'.jpg'&&c('data:image/png;base64,AAAA')=='data:image/png;base64,AAAA'&&c('https://evil.example/'+h+'.jpg')===''&&c('%s/x.jpg')===''&&c('%s/'+h+'.jpg?a=1')===''&&c('%s.evil.com/'+h+'.jpg')===''
      &&cleanEnt('n',{t:'p',img:'%s/'+h+'.jpg',im:[{img:'https://evil.example/'+h+'.jpg',g:''}]}).im[0].img===''}"""%((PH,)*6)))
    # ── 문서 안에 남은 사진 옮기기
    DATA=A.evaluate("()=>{const c=document.createElement('canvas');c.width=c.height=8;c.getContext('2d').fillRect(0,0,4,4);return c.toDataURL('image/jpeg')}")
    A.evaluate("(d)=>{const o=nd('%s');o.im=[{img:d,g:''}];nd('%s').img=d;upd(nd('%s'));sv()}"%(pi,gid,gid),DATA);settle(A,1500)
    A.click('#bk');settle(A,400)
    ok('P10 공유 창에 "사진 서버로 옮기기" 버튼과 남은 장수가 보임',A.locator('[data-da=mv]').count()==1 and '2장' in A.inner_text('#dl'))
    A.click('[data-da=mv]');settle(A,3000)
    ok('P11 옮기면 모두 서버 주소가 되고 서버 DB·다른 사람 화면에도 반영, 버튼은 사라짐',A.evaluate("([p,g])=>dataImgs().length==0&&nd(p).im[0].img.startsWith('%s/')&&nd(g).img.startsWith('%s/')"%(PH,PH),[pi,gid]) and same(A,B,room=room) and 'base64' not in json.dumps(api('/dump?room='+room)) and A.locator('[data-da=mv]').count()==0)
    # ── 파일 저장: 사진 서버 주소는 사진 자체(data URL)로 바꿔 넣어 파일 하나로 완결
    with A.expect_download() as d: A.evaluate("dlFile('backup')")
    doc=json.load(open(d.value.path(),encoding='utf-8'));imgs=[n.get('img') for n in doc['nodes'] if n.get('img')]+[x['img'] for n in doc['nodes'] for x in n.get('im',[])]
    ok('P12 저장한 파일에는 서버 주소 대신 사진이 들어 있음(%d장)'%len(imgs),len(imgs)>=3 and all(i.startswith('data:image/jpeg') for i in imgs) and PH not in json.dumps(doc))
    # ── "옮겼습니다"는 서버에 저장이 끝난 뒤에 뜸(저장은 비동기 — 예전엔 메시지가 먼저 떠서 직후 새로고침하면 사진이 되돌아왔음)
    def reseed(): A.evaluate("(d)=>{nd('%s').img=d;upd(nd('%s'));sv()}"%(gid,gid),DATA);settle(A,1500)
    def moveAndWait(txt,tries=80):
        A.evaluate("dlShow('')");A.click('#bk');settle(A,400);A.click('[data-da=mv]')
        for i in range(tries):
            if txt in A.inner_text('#dl'):return True
            settle(A,500)
        return False
    reseed();A.evaluate("window.__rpcDelay=3000");shown=moveAndWait('장을 옮겼');has=lambda:'base64' in json.dumps(api('/dump?room='+room))
    ok('P13 저장이 느려도 "옮겼습니다"가 뜰 땐 서버에 이미 저장돼 있음(직후 새로고침해도 안전)',shown and not has())
    A.evaluate("window.__rpcDelay=0");reseed()
    A.route('**/rpc/apply_ops',lambda r:r.abort());shown=moveAndWait('아직 저장되지 않았',tries=90)
    ok('P14 서버에 저장이 안 되면 "옮겼습니다" 대신 아직 저장되지 않았다고 알림',shown and '옮겼습니다' not in A.inner_text('#dl') and '남은 변경' in A.inner_text('#dl') and has())
    A.unroute('**/rpc/apply_ops');ok_=False
    for i in range(40):
        settle(A,500)
        if not has():ok_=True;break
    ok('P15 서버가 돌아오면 백그라운드 재시도로 저장이 끝남',ok_)
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    if ERR: print(ERR[:3])
    b.close()
