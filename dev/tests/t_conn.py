# 연결 안정성: 탭을 오래 비웠다 와도 멀쩡한 연결은 건드리지 않음, 다시 맞출 땐 새로 바뀐 것만 받음, 방장 문서 선점 방지, 사람 수에 따른 커서 전송 간격
from playwright.sync_api import sync_playwright
from helpers import *
cnt=lambda pg:pg.evaluate('window.__chanCount||0'); label=lambda pg:pg.inner_text('#bk .bt')
HID="Object.defineProperty(document,'visibilityState',{value:'hidden',configurable:true});document.dispatchEvent(new Event('visibilitychange'))"
VIS="Object.defineProperty(document,'visibilityState',{value:'visible',configurable:true});document.dispatchEvent(new Event('visibilitychange'))"
def sweep(pg,n=12):
    pg.mouse.move(300,300)
    for i in range(n):pg.mouse.move(300+i*30,300+(i%3)*20);pg.wait_for_timeout(60)
with sync_playwright() as p:
    b=p.chromium.launch();A=client(b);B=client(b)
    reqA=[];A.on('request',lambda r:reqA.append(r.url))
    A.goto(URL);settle(A,500)
    # C1 혼자일 땐 커서를 서버로 보내지 않음(메시지 한도 절약)
    A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    reqA.clear();sweep(A);settle(A,300)
    ok('C1 혼자일 땐 커서 메시지를 안 보냄',not any('/bcast' in u for u in reqA))
    B.goto(URL+h);settle(B,1800)
    # C2 사람이 늘면 커서 전송 간격이 길어짐: 같은 시간 움직여도 2명일 때보다 4명일 때 덜 보냄
    reqA.clear();sweep(A,15);settle(A,300);n2=sum('/bcast' in u for u in reqA)
    C=client(b);D=client(b);C.goto(URL+h);D.goto(URL+h);settle(C,1800);settle(D,1200)
    reqA.clear();sweep(A,15);settle(A,300);n4=sum('/bcast' in u for u in reqA)
    ok('C2 2명일 때 커서를 보냄(%d개)'%n2,n2>=4)
    ok('C3 4명일 땐 더 드물게 보냄(%d개 < %d개의 절반)'%(n4,n2),n4*2<=n2)
    C.context.close();D.context.close()
    A.evaluate("document.querySelectorAll('.rc').forEach(x=>x.remove())")
    # C4 멀쩡한 연결로 10초 넘게 탭을 비웠다 와도 새로 연결하지 않고 "다시 연결 중…" 도 안 뜸
    settle(A,2500);c0=cnt(A);A.evaluate(HID)
    B.evaluate("nd('c').name='A가 숨은 동안 B가 바꿈';upd(nd('c'));sv()");settle(A,11500)
    A.evaluate(VIS);A.wait_for_timeout(150);l=label(A);settle(A,2500)
    ok('C4 연결이 멀쩡하면 오래 비웠다 와도 재연결·깜빡임 없음',cnt(A)==c0 and l=='링크 복사' and label(A)=='링크 복사')
    ok('C5 놓친 변경은 반영됨',same(A,B,room=room))
    ok('C6 라이브러리 채널 목록에 채널이 하나만 남음',A.evaluate("sb.getChannels().length")==1)
    # C7 다시 맞출 땐 새로 바뀐 것만 받음(큰 방에서 사진까지 전부 다시 받지 않음)
    A.evaluate("""async()=>{for(let r=0;r<5;r++){const ops=[];for(let i=0;i<500;i++)ops.push({k:'n',id:'a',set:{desc:'v'+r+'_'+i}});await sb.rpc('apply_ops',{p_room:rid,p_ops:ops})}}""");settle(A,4000)
    reqA.clear();A.evaluate(HID);A.wait_for_timeout(200);A.evaluate(VIS);settle(A,1500)
    gt=[int(u.split('gt=')[1].split('&')[0]) for u in reqA if '/items?' in u]
    ok('C7 다시 맞출 때 번호(ver) 이후 것만 요청(%s)'%gt,len(gt)>=1 and all(g>100 for g in gt))
    ok('C8 그래도 B 와 같은 상태',same(A,B,room=room))
    # C9 방장이 문서를 올리기 전에 손님이 먼저 들어와도 방장 문서가 사라지지 않음
    E=client(b);F=client(b)
    E.goto(URL);settle(E,500);E.evaluate("window.__rpcDelay=1200");E.click('#bk');E.wait_for_timeout(300)
    h2=E.evaluate('location.hash');F.goto(URL+h2);settle(F,1500)
    settle(E,7000);room2=h2.split('room=')[1]
    ok('C9 방장 문서가 손님에게 먼저 선점당하지 않음',E.evaluate("S.nodes.length")>=4 and same(E,F,room=room2) and F.evaluate("S.nodes.length")==E.evaluate("S.nodes.length"))
    # C12 다시 맞추기·폴링의 목록 요청은 내용(사진) 없이 번호만 받음 — 새 번호가 없으면 내용 요청은 0번
    reqA.clear();settle(A,9000);il=[u for u in reqA if '/items?' in u]
    ok('C12 새 변경이 없으면 폴링은 번호만 받는 요청뿐(%d번)'%len(il),len(il)>=1 and all('light=1' in u for u in il))
    # C10 변경은 Broadcast 로 바로 전달됨(폴링 4초보다 훨씬 빠르고, 폴링이 대신 받은 게 아님)
    E.evaluate("window.__rpcDelay=0");settle(E,500);m0=F.evaluate("window.__missed");E.evaluate("nd('b').name='브로드캐스트로 전달';upd(nd('b'));sv()");settle(F,1200)
    ok('C10 변경이 1.2초 안에 전달됨(폴링 아님)',F.evaluate("nd('b').name")=='브로드캐스트로 전달' and F.evaluate("window.__missed")==m0)
    # C11 실시간 전달이 모두 빠져도(연결은 멀쩡해 보임) 폴링이 5초 안팎에 따라잡고 놓쳤다고 기록함
    m1=F.evaluate("window.__missed");F.evaluate("window.__noBc=true;window.__noPg=true");E.evaluate("nd('b').name='이벤트 없이 전달되어야 함';upd(nd('b'));sv()");settle(F,6500)
    ok('C11 실시간이 빠져도 폴링이 6초 안에 따라잡고 놓쳤다고 기록함',F.evaluate("nd('b').name")=='이벤트 없이 전달되어야 함' and F.evaluate("window.__missed")>m1)
    # C13 위치만 바꿀 땐 사진을 서버 응답·Broadcast 에 싣지 않음(egress), 사진을 바꿀 땐 통째로 전달, 받는 쪽 사진은 그대로
    F.evaluate("window.__noBc=false;window.__noPg=false");IMGD="data:image/png;base64,"+"A"*3000
    bc=[];rsp=[];E.on('request',lambda r:bc.append(r.post_data or '') if '/bcast' in r.url else None);E.on('response',lambda r:rsp.append(r) if 'apply_ops' in r.url else None)
    E.evaluate("nd('b').img=%r;upd(nd('b'));sv()"%IMGD);settle(E,1800)
    ok('C13a 사진을 바꾸면 상대에게도 사진이 전달됨',F.evaluate("nd('b').img")==IMGD)
    bc.clear();rsp.clear();E.evaluate("nd('b').x+=40;upd(nd('b'));sv()");settle(E,1800)
    bodies=[r.text() for r in rsp]
    ok('C13b 위치만 바꿀 땐 Broadcast 에 사진이 없음(%d번 전송)'%len([b for b in bc if '"kind"' in b]),any('"kind"' in b for b in bc) and not any('AAAAAAAA' in b for b in bc))
    ok('C13c 서버 응답에도 사진이 없음',len(bodies)>=1 and not any('AAAAAAAA' in b for b in bodies))
    ok('C13d 그래도 받는 쪽 사진·위치는 정상',F.evaluate("nd('b').img")==IMGD and F.evaluate("nd('b').x")==E.evaluate("nd('b').x") and same(E,F,room=room2))
    print('errors:',ERR[:4]);b.close()
