# 방 문서 브라우저 캐시(IndexedDB): 다시 들어올 때 문서 전체(사진 포함)를 또 받지 않고 바뀐 것만 받음
from playwright.sync_api import sync_playwright
from helpers import *
HID="Object.defineProperty(document,'visibilityState',{value:'hidden',configurable:true});document.dispatchEvent(new Event('visibilitychange'))"
IMGD="data:image/png;base64,"+"A"*3000
# 캐시된 행 읽기: {id: 행}
IDB="""()=>new Promise(ok=>{const q=indexedDB.open('relmap');q.onerror=()=>ok({});q.onsuccess=()=>{const t=q.result.transaction('rows'),s=t.objectStore('rows'),r=s.getAll(IDBKeyRange.bound(rid+'|',rid+'|\\uffff'));t.oncomplete=()=>ok(Object.fromEntries(r.result.map(x=>[x.kind+':'+x.id,x])))}})"""
# 캐시된 행의 번호를 크게 부풀림(서버가 되돌려진 상황 흉내)
BUMP="""()=>new Promise(ok=>{const q=indexedDB.open('relmap');q.onsuccess=()=>{const t=q.result.transaction('rows','readwrite'),s=t.objectStore('rows'),r=s.openCursor(IDBKeyRange.bound(rid+'|',rid+'|\\uffff'));r.onsuccess=()=>{const c=r.result;if(!c)return;const v=c.value;v.ver+=1e9;c.update(v);c.continue()};t.oncomplete=()=>ok(1)}})"""
def rejoin(pg,h):
    pg.goto('about:blank'); pg.goto(URL+h)   # 같은 주소로 goto 하면 새로고침이 안 되므로 빈 페이지를 거침
def full(u): return 'light=0&ids=&' in u            # 문서 전체(사진 포함)를 받는 요청
def byid(u): return 'light=0&ids=' in u and not full(u)   # 새 행만 id 로 받는 요청
with sync_playwright() as p:
    b=p.chromium.launch();A=client(b);B=client(b)
    reqA=[];A.on('request',lambda r:reqA.append(r.url) if '/items?' in r.url else None)
    A.goto(URL);settle(A,500);A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    A.evaluate("nd('b').img=%r;upd(nd('b'));sv()"%IMGD);settle(A,1500);B.goto(URL+h);settle(B,1800)
    n=A.evaluate("S.nodes.length+S.links.length");settle(A,2500)
    c=A.evaluate(IDB)
    ok('K1 처음 들어오면 문서가 캐시에 저장됨(%d/%d개)'%(len(c),n),len(c)==n and c.get('n:b',{}).get('data',{}).get('img')==IMGD)
    # 탭을 숨기면 2초를 기다리지 않고 바로 저장
    A.evaluate("nd('c').name='숨기기 직전 변경';upd(nd('c'));sv()");settle(A,700);A.evaluate(HID);A.wait_for_timeout(400)
    ok('K2 탭을 숨길 때 바로 저장됨',A.evaluate(IDB)['n:c']['data'].get('name')=='숨기기 직전 변경')
    # 닫힌 동안 남이 바꾸고(이름·삭제) 다시 들어옴
    A.goto('about:blank');B.evaluate("nd('c').name='닫힌 동안 B가 바꿈';upd(nd('c'));sv()");settle(B,800)
    B.evaluate("select('e');del()");settle(B,500)
    reqA.clear();A.goto(URL+h);settle(A,2500)
    ok('K3 다시 들어올 땐 문서 전체를 받지 않음(%d번 요청)'%len(reqA),not any(full(u) for u in reqA) and len(reqA)>=1)
    ok('K4 닫힌 동안 바뀐 것(이름·삭제)은 반영됨',A.evaluate("nd('c').name")=='닫힌 동안 B가 바꿈' and A.evaluate("!nd('e')") and same(A,B,room=room))
    ok('K5 사진은 캐시에서 그대로 보임(다시 받지 않음)',A.evaluate("nd('b').img")==IMGD and not any(byid(u) and 'b' in u.split('ids=')[1].split('&')[0].split(',') for u in reqA))
    # 서버가 되돌려져 캐시 번호가 서버보다 크면 캐시를 버리고 전부 새로 받음
    A.evaluate(BUMP);reqA.clear();rejoin(A,h);settle(A,2500)
    ok('K6 서버보다 번호가 큰 캐시는 버리고 전부 새로 받음',any(full(u) for u in reqA) and same(A,B,room=room))
    settle(A,2500);ok('K7 버린 뒤 새 문서가 다시 캐시됨',all(x['ver']<1e8 for x in A.evaluate(IDB).values()) and len(A.evaluate(IDB))>=n-1)
    # 캐시된 값도 검증을 거침(손으로 넣은 위험한 값)
    A.evaluate("""()=>new Promise(ok=>{const q=indexedDB.open('relmap');q.onsuccess=()=>{const t=q.result.transaction('rows','readwrite');t.objectStore('rows').put({kind:'n',id:'zz',ver:5,deleted:false,data:{t:'p',x:10,y:10,name:'<img src=x onerror=window.__x=1>',col:'red;background:url(javascript:1)'}},rid+'|n:zz');t.oncomplete=()=>ok(1)}})""")
    rejoin(A,h);settle(A,2500)
    ok('K8 캐시 행도 검증됨(스크립트 실행 안 됨, 이상한 색은 버림)',not A.evaluate("window.__x") and A.evaluate("!document.querySelector('img[src=\"x\"]')") and A.evaluate("(()=>{const o=nd('zz');return !o||!o.col||/^#[0-9a-f]{3,8}$/i.test(o.col)})()"))
    # 캐시를 못 쓰는 환경(IndexedDB 없음)에서도 그대로 동작
    G=client(b,"Object.defineProperty(window,'indexedDB',{value:undefined,configurable:true});");G.goto(URL+h);settle(G,2500)
    ok('K9 IndexedDB 가 없어도 전부 받아서 정상 동작',G.evaluate("S.nodes.length")>=4 and G.evaluate("nd('c').name")=='닫힌 동안 B가 바꿈')
    # 같은 방을 연 다른 탭이 더 새 행을 이미 저장했으면, 늦게 저장하는 옛 상태가 덮어쓰지 않음
    A.evaluate("""()=>new Promise(ok=>{const q=indexedDB.open('relmap');q.onsuccess=()=>{const t=q.result.transaction('rows','readwrite'),s=t.objectStore('rows'),k=rid+'|n:c',g=s.get(k);g.onsuccess=()=>{const v=g.result;v.ver=1e6;v.data.name='다른 탭이 저장한 더 새 값';s.put(v,k)};t.oncomplete=()=>{cMark(['n:c']);cFlush();ok(1)}}})""");settle(A,500)
    ok('K10 더 새 번호의 캐시 행은 옛 상태가 덮어쓰지 않음',A.evaluate(IDB)['n:c']['ver']==1e6)
    ok('페이지 오류 없음',not ERR);
    if ERR: print(ERR[:3])
    b.close()
