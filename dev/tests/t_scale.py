# 측정용(통과/실패 아님): python tests/t_scale.py 6  — 서버·DB 를 띄운 상태에서 실행.
# 여러 명이 동시에 인물을 끌 때 각자 화면이 얼마나 바쁜지(처리 횟수·시간), 다 같은 상태로 모이는 데 걸리는 시간
import sys,time
from playwright.sync_api import sync_playwright
from helpers import *
N=int(sys.argv[1]) if len(sys.argv)>1 else 6
INST="""window.__m={diffN:0,diffMs:0,ing:0,lt:0,ev:0};{const d0=diff;window.diff=function(...a){const t=performance.now(),r=d0.apply(this,a);__m.diffMs+=performance.now()-t;__m.diffN++;return r};
const i0=ingestMany;window.ingestMany=function(...a){__m.ing++;return i0.apply(this,a)};
try{new PerformanceObserver(l=>l.getEntries().forEach(e=>__m.lt+=e.duration)).observe({entryTypes:['longtask']})}catch(e){}}"""
with sync_playwright() as p:
    b=p.chromium.launch();P=[client(b) for _ in range(N)]
    A=P[0];A.goto(URL);settle(A,500)
    A.evaluate("for(let i=0;i<120;i++){const n={id:'x'+i,t:'p',x:200+(i%12)*110,y:150+Math.floor(i/12)*110,name:'사람'+i};S.nodes.push(n);mk(n)}sv()");settle(A,800)
    A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    for q in P[1:]:q.goto(URL+h);settle(q,1200)
    settle(A,1000)
    for q in P:q.evaluate(INST)
    boxes=[(lambda r:{'x':r['x']+r['width']/2-40,'y':r['y']+r['height']/2-40})(q.locator(f'.p[data-id="x{i}"] .im').bounding_box()) for i,q in enumerate(P)]
    for i,q in enumerate(P):q.mouse.move(boxes[i]['x']+40,boxes[i]['y']+40);q.mouse.down()
    t0=time.time()
    for s in range(60):
        for i,q in enumerate(P):q.mouse.move(boxes[i]['x']+40+s*2,boxes[i]['y']+40+(s%20)*3)
    for q in P:q.mouse.up()
    t1=time.time();tm=time.time()
    for _ in range(100):
        st=[canon(norm(local(q))) for q in P]
        if all(x==st[0] for x in st):break
        P[0].wait_for_timeout(100)
    conv=time.time()-t1
    print(f'사람 {N}명: 끄는 시간 {t1-t0:.1f}s, 끝난 뒤 모두 같아지기까지 {conv:.1f}s')
    for i,q in enumerate(P):
        m=q.evaluate('__m');print(f'  클라이언트{i}: diff {m["diffN"]}번 {m["diffMs"]:.0f}ms, 이벤트 처리 {m["ing"]}번, 긴 작업 합계 {m["lt"]:.0f}ms, apply_ops {q.evaluate("window.__rpcCount||0")}번')
    print('PASS 수렴',all(x==st[0] for x in st))
    b.close()
