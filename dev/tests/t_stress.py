import json, random, urllib.request
from playwright.sync_api import sync_playwright
from helpers import *
random.seed(7)
FIELDS=[('name',lambda i,w:f"{w}{i}"),('desc',lambda i,w:f"{w}-desc{i}"),('x',lambda i,w:random.randint(-300,300)),('y',lambda i,w:random.randint(-300,300)),('col',lambda i,w:random.choice(['#0066FF','#00BF40','#FF4242','#F553DA']))]
with sync_playwright() as p:
    b=p.chromium.launch();A=client(b);B=client(b)
    A.goto(URL);settle(A,500);A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    B.goto(URL+h);settle(B,1800);api('/ctl',{'delay':20,'jitter':80})
    bad=0;N=30
    for i in range(N):
        A.evaluate(f"window.__rpcDelay={random.choice([0,50,200,400])}");B.evaluate(f"window.__rpcDelay={random.choice([0,50,200,400])}")
        for w,pg in (('A',A),('B',B)):
            for _ in range(random.randint(1,3)):
                nid=random.choice(['b','c','d']);f,g=random.choice(FIELDS);v=g(i,w)
                pg.evaluate(f"(()=>{{const n=nd('{nid}');if(!n)return;n.{f}={json.dumps(v)};upd(n);sv()}})()");pg.wait_for_timeout(random.choice([0,10,40,90]))
        if i%7==3:   # 가끔 추가/삭제도 동시에
            A.evaluate("addNode('p',{x:Math.random()*300,y:Math.random()*300})") if False else A.click('button[data-t="p"]')
            B.evaluate("(()=>{const l=S.links[0];if(l){S.links=S.links.filter(x=>x!=l);sv()}})()")
        settle(A,2600+400)
        if not same(A,B,room=room):
            bad+=1;settle(A,3000)
            print(f'#{i} 갈라짐',' → 3초 뒤에도' if not same(A,B,room=room) else ' → 3초 뒤 수렴')
    print(f'diverged {bad}/{N}');print(ERR[:3]);b.close()
