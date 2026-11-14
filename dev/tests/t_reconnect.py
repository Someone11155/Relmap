import json, urllib.request
from playwright.sync_api import sync_playwright
from helpers import *
cnt=lambda pg:pg.evaluate('window.__chanCount||0'); label=lambda pg:pg.inner_text('#bk .bt')
ok=lambda n,v:print(('PASS ' if v else 'FAIL ')+n)
HID="Object.defineProperty(document,'visibilityState',{value:'hidden',configurable:true});document.dispatchEvent(new Event('visibilitychange'))"
VIS="Object.defineProperty(document,'visibilityState',{value:'visible',configurable:true});document.dispatchEvent(new Event('visibilitychange'))"
with sync_playwright() as p:
    b=p.chromium.launch();A=client(b);B=client(b)
    A.goto(URL);settle(A,500);A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    B.goto(URL+h);settle(B,1800)
    ok('R0 정상 연결',label(A)=='링크 복사' and same(A,B,room=room))
    # R1 서버가 채널을 닫음(CLOSED) — 라이브러리는 자동 재연결하지 않는 경우
    c0=cnt(A);A.evaluate("__sbKill('CLOSED')");A.wait_for_timeout(120);l1=label(A)
    B.evaluate("nd('c').name='연결 끊긴 동안 B가 바꿈';upd(nd('c'));sv()");settle(A,2500)
    ok('R1a 끊기면 "다시 연결 중…" 표시',l1=='다시 연결 중…')
    ok('R1b 새 채널로 자동 재연결, 상태 복구',cnt(A)==c0+1 and label(A)=='링크 복사')
    ok('R1c 끊긴 동안 놓친 변경이 재연결 후 반영되어 동일',same(A,B,room=room))
    A.mouse.move(500,300);A.mouse.move(700,420,steps=5);settle(B,800)
    ok('R1d 재연결 뒤 커서·접속자 표시 정상',B.locator('.rc').count()==1 and B.locator('#pp .pc').count()==2)
    # R6 연결이 끊긴 동안의 내 편집도 저장·전달됨
    A.evaluate("__sbKill('CLOSED')");A.evaluate("nd('b').desc='끊긴 동안 A가 쓴 설명';upd(nd('b'));sv()");settle(A,3000)
    ok('R6 연결 끊긴 동안 내 편집도 저장되어 B·DB 에 반영',same(A,B,room=room) and label(A)=='링크 복사')
    # R2 오류 상태에서 복구되지 않을 때(6초 뒤 새로 연결)
    c0=cnt(A);A.evaluate("__sbKill('CHANNEL_ERROR')");A.wait_for_timeout(200);l2=label(A);settle(A,8000)
    ok('R2 오류가 계속되면 6초 뒤 새로 연결',l2=='다시 연결 중…' and cnt(A)==c0+1 and label(A)=='링크 복사')
    # R3 백그라운드(10초 넘게) 후 복귀: 소켓이 조용히 죽어 있어도 새로 연결 + 놓친 변경 반영
    c0=cnt(A);A.evaluate(HID);A.evaluate("__sbDrop(999999)")   # 조용히 끊김(상태는 아직 joined 로 보임)
    B.evaluate("nd('d').desc='A가 백그라운드일 때 B가 바꿈';upd(nd('d'));sv()");settle(A,11500)
    A.evaluate(VIS);settle(A,2500)
    ok('R3 10초 넘는 백그라운드 후 복귀하면 새로 연결하고 놓친 변경 반영',cnt(A)==c0+1 and label(A)=='링크 복사' and same(A,B,room=room))
    # R3b 잠깐(2초) 나갔다 오면 재연결 없이 다시 맞추기만
    c0=cnt(A);A.evaluate(HID);A.wait_for_timeout(2000);A.evaluate(VIS);settle(A,1200)
    ok('R3b 짧게 나갔다 오면 불필요한 재연결 없음',cnt(A)==c0 and label(A)=='링크 복사')
    # R4 네트워크 복귀(online)
    c0=cnt(A);A.evaluate("window.dispatchEvent(new Event('online'))");settle(A,2000)
    ok('R4 네트워크가 돌아오면(online) 새로 연결',cnt(A)==c0+1 and label(A)=='링크 복사')
    # R5 안정성: 재연결 후 불필요한 반복 없음, 교체된 옛 채널의 CLOSED 는 무시
    c0=cnt(A);settle(A,8000)
    ok('R5 재연결 루프 없이 안정(옛 채널의 CLOSED 알림 무시)',cnt(A)==c0 and label(A)=='링크 복사' and same(A,B,room=room))
    # R7 나가기는 재연결을 시도하지 않음
    c0=cnt(A);A.click('#bx');settle(A,3000)
    ok('R7 직접 나가면 재연결하지 않음',cnt(A)==0 or cnt(A)<=c0)   # 새로고침되어 카운터 초기화
    print('errors:',ERR[:4]);b.close()
