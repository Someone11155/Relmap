import json, urllib.request
from playwright.sync_api import sync_playwright
from helpers import *
def nm(pg):return pg.evaluate("nd('c').name")
with sync_playwright() as p:
    b=p.chromium.launch();A=client(b);B=client(b)
    A.goto(URL);settle(A,500);A.click('#bk');settle(A,1500);h=A.evaluate('location.hash');room=h.split('room=')[1]
    B.goto(URL+h);settle(B,1800)
    bad=0
    for i in range(40):
        A.evaluate(f"nd('c').name='A{i}';upd(nd('c'));sv()");B.evaluate(f"nd('c').name='B{i}';upd(nd('c'));sv()");settle(A,1800)
        a,bb=nm(A),nm(B);db=[r for r in api('/dump?room='+room)['data'] if r['id']=='c'][0]['data']['name']
        if not(a==bb==db):
            bad+=1;print(f'#{i} DIVERGED  A={a} B={bb} DB={db}')
            settle(A,3000);print('   3초 뒤:',nm(A),nm(B),[r for r in api("/dump?room="+room)["data"] if r["id"]=="c"][0]["data"]["name"])
    print('diverged',bad,'/ 40');print(ERR[:3]);b.close()
