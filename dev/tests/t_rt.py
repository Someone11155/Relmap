# 실시간 중계 서버(Cloudflare Durable Object 방식): Supabase Realtime 대신 WebSocket 중계로 커서·접속자·문서 변경을 주고받음
# 중계 규칙은 worker/relay.mjs 진짜 코드를 dev/fakesb.mjs 가 8792 포트에 올려 씀(Durable Object 껍데기 rt.mjs 만 Cloudflare 에서만 돌아가 테스트 못 함)
from playwright.sync_api import sync_playwright
from helpers import *
RT = 'ws://localhost:8792'; PRE = "localStorage.setItem('relmap_rt','%s');" % RT
HID = "Object.defineProperty(document,'visibilityState',{value:'hidden',configurable:true});document.dispatchEvent(new Event('visibilitychange'))"
VIS = "Object.defineProperty(document,'visibilityState',{value:'visible',configurable:true});document.dispatchEvent(new Event('visibilitychange'))"
label = lambda pg: pg.inner_text('#bk .bt')
def sweep(pg, n=12):
    pg.mouse.move(300, 300)
    for i in range(n): pg.mouse.move(300 + i * 30, 300 + (i % 3) * 20); pg.wait_for_timeout(60)
# 페이지 안에서 직접 여는 WebSocket(앱을 거치지 않고 서버 규칙만 확인): 로그인 토큰을 보내고(token=None 이면 안 보냄) 받은 글을 window[name] 에 쌓음
RAW = """([name,key,token])=>new Promise(res=>{const w=window[name+'_w']=new WebSocket('%s/room/'+rid+'?k='+key),log=window[name]=[];w.onmessage=e=>log.push(e.data);w.onclose=e=>log.push('CLOSE'+e.code);
  w.onopen=()=>{if(token!==null)w.send(JSON.stringify({t:'auth',token}));res(1)}})"""%RT
with sync_playwright() as p:
    b = p.chromium.launch(); A = client(b, PRE); B = client(b, PRE)
    sentA = []; reqA = []
    A.on('websocket', lambda w: w.on('framesent', lambda f: sentA.append(f if isinstance(f, str) else str(f))))
    A.on('request', lambda r: reqA.append(r.url))
    A.goto(URL); settle(A, 500); A.click('#bk'); settle(A, 1500); h = A.evaluate('location.hash'); room = h.split('room=')[1]
    ok('R1 중계 서버로 연결됨(Supabase 실시간 채널은 안 만듦)', A.evaluate("chan instanceof RtChan&&chan.state=='joined'&&sb.getChannels().length==0") and label(A) == '링크 복사')
    sentA.clear(); sweep(A); settle(A, 300)
    ok('R2 혼자일 땐 커서를 보내지 않음', not any('"cur"' in f for f in sentA))
    B.goto(URL + h); settle(B, 1800)
    ok('R3 접속자 목록: 서로 보이고 이름이 전달됨', A.evaluate("others().length") == 1 and B.evaluate("others().length") == 1 and A.evaluate("others()[0].presence.name") == B.evaluate("me.name"))
    B.evaluate("me.name='바뀐 이름';trackMe();renderOthers()"); settle(B, 500)
    ok('R4 이름을 바꾸면 상대 화면의 접속자 정보가 바뀜', A.evaluate("others()[0].presence.name") == '바뀐 이름')
    m0 = B.evaluate("window.__missed"); A.evaluate("nd('c').name='중계로 전달';upd(nd('c'));sv()"); settle(B, 1000)
    ok('R5 문서 변경이 1초 안에 중계로 전달됨(폴링 아님)', B.evaluate("nd('c').name") == '중계로 전달' and B.evaluate("window.__missed") == m0 and same(A, B, room=room))
    sweep(A); settle(B, 500)
    ok('R6 커서가 상대 화면에 전달됨', B.evaluate("curPos.size") >= 1 and any('"cur"' in f for f in sentA))
    D = client(b, PRE); D.goto(URL + h); settle(D, 1800); n1 = A.evaluate("others().length"); D.context.close(); settle(A, 1500)
    ok('R7 접속한 사람이 나가면 접속자 목록에서 빠짐(%d→%d)' % (n1, A.evaluate("others().length")), n1 == 2 and A.evaluate("others().length") == 1)
    # 서버가 연결을 끊어도 자동으로 다시 붙음
    A.evaluate("window.__c=chan"); api('/rtkill'); settle(A, 3500)
    ok('R8 서버가 연결을 끊어도 새 연결로 다시 붙음', A.evaluate("chan!==window.__c&&chan.state=='joined'") and label(A) == '링크 복사')
    A.evaluate("nd('c').name='재연결 뒤 변경';upd(nd('c'));sv()"); settle(B, 1500)
    ok('R9 다시 붙은 뒤에도 변경·접속자가 전달됨', B.evaluate("nd('c').name") == '재연결 뒤 변경' and A.evaluate("others().length") == 1 and B.evaluate("others().length") == 1 and same(A, B, room=room))
    # 멀쩡한 연결은 탭을 오래 비웠다 와도 건드리지 않음
    A.evaluate("window.__c2=chan"); A.evaluate(HID); settle(A, 11500); A.evaluate(VIS); settle(A, 2000)
    ok('R10 멀쩡한 연결은 오래 비웠다 와도 재연결·깜빡임 없음', A.evaluate("chan===window.__c2&&chan.state=='joined'") and label(A) == '링크 복사')
    # 응답 없는 죽은 연결(서버가 글을 다 무시)은 돌아왔을 때 감지해서 새로 연결을 시도하고, 서버가 살아나면 붙음
    api('/ctl', {'mute': True}); A.evaluate("window.__c3=chan"); A.evaluate(HID); A.wait_for_timeout(200); A.evaluate(VIS); settle(A, 5200)
    ch = A.evaluate("chan!==window.__c3"); api('/ctl', {'mute': False}); up = False
    for i in range(30):
        settle(A, 1000)
        if A.evaluate("chan.state=='joined'") and label(A) == '링크 복사': up = True; break
    ok('R11 응답 없는 연결은 감지해 새로 연결하고, 서버가 살아나면 다시 붙음', ch and up)
    # 35초 넘게 아무 소리가 없는 연결은 끊긴 것으로 봄(12초마다 확인)
    A.evaluate("window.__c4=chan;chan.lp=Date.now()-40000"); settle(A, 16000)
    ok('R12 오래 조용한 연결은 끊긴 것으로 보고 새로 연결함', A.evaluate("chan!==window.__c4&&chan.state=='joined'"))
    # 서버 규칙: 로그인 확인, 허용된 글만 전달
    r = A.evaluate("""()=>new Promise(res=>{const w=new WebSocket('%s/room/'+rid+'?k=raw1'),log=[];w.onopen=()=>w.send(JSON.stringify({t:'auth',token:'bad'}));w.onmessage=e=>log.push(e.data);w.onclose=e=>res([e.code,log])})""" % RT)
    ok('R13 로그인 토큰이 틀리면 4401 로 닫히고 아무것도 못 받음', r[0] == 4401 and r[1] == [])
    A.evaluate(RAW, ['rawU', 'raw2', None]); A.evaluate("rawU_w.send(JSON.stringify({t:'b',e:'cur',p:{k:'evil',c:{x:5,y:5}}}))"); settle(A, 500)
    ok('R14 로그인 전에 보낸 글은 전달되지 않고 연결이 닫힘', 'CLOSE4401' in A.evaluate("rawU") and not B.evaluate("curPos.has('evil')"))
    A.evaluate(RAW, ['rawL', 'rawl', 'fk_l']); A.evaluate(RAW, ['rawS', 'raws', 'fk_s']); settle(A, 400)
    A.evaluate("""()=>{rawS_w.send('ping');rawS_w.send(JSON.stringify({t:'b',e:'evil',p:1}));rawS_w.send(JSON.stringify({t:'b',e:'rows',p:'x'.repeat(400000)}));rawS_w.send('not json');rawS_w.send(JSON.stringify({t:'b',e:'cur',p:{k:'zz',c:{x:1,y:2}}}))}"""); settle(A, 600)
    got = [x for x in A.evaluate("rawL") if x.startswith('{"t":"b"')]
    ok('R15 허용된 이벤트(cur·rows)만, 크기 제한 안에서 전달되고 ping 에는 pong 이 옴', len(got) == 1 and '"cur"' in got[0] and 'pong' in A.evaluate("rawS") and B.evaluate("curPos.has('zz')"))
    # 처음 연결부터 실패하면(주소 오류) 알림
    Cx = client(b, "localStorage.setItem('relmap_rt','ws://localhost:1');"); Cx.goto(URL); settle(Cx, 500); Cx.click('#bk'); settle(Cx, 3000)
    dl = [e for e in ERR if '실시간 중계 서버' in e]; ERR[:] = [e for e in ERR if '실시간 중계 서버' not in e]
    ok('R16 처음부터 연결에 실패하면 원인을 알려 주는 안내가 뜸', len(dl) == 1 and 'REALTIME' in dl[0])
    ok('R17 이 모든 동안 Supabase 실시간(채널·이벤트 요청)은 한 번도 안 씀', not any('/bcast' in u or '/events' in u for u in reqA))
    ok('Z 페이지 오류·예상 못한 대화상자 없음', not ERR)
    if ERR: print(ERR[:3])
    b.close()
