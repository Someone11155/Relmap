from helpers import *
ok=lambda name,v:print(('PASS ' if v else 'FAIL ')+name)
with sync_playwright() as p:
    b=p.chromium.launch()
    A=client(b);B=client(b)
    A.goto(URL);settle(A,500);A.click('#bk');settle(A,1500)
    h=A.evaluate('location.hash');room=h.split('room=')[1]
    rows=api('/dump?room='+room)['data']
    ok('T1 방 생성·시드: DB에 인물5+선2',len(rows)==7 and A.eval_on_selector('#bk .bt','e=>e.textContent')=='링크 복사')
    B.goto(URL+h);settle(B,1800)
    ok('T2 입장자는 DB 문서를 받음(동일)',same(A,B,room=room))
    # T3 드래그
    box=A.locator('.p[data-id="b"] .im').bounding_box();A.mouse.move(box['x']+40,box['y']+40);A.mouse.down();A.mouse.move(box['x']-70,box['y']+120,steps=12);A.mouse.up();settle(A)
    ok('T3 드래그가 B와 DB에 반영',same(A,B,room=room))
    # T4 서로 다른 필드 동시 수정
    A.evaluate("nd('c').desc='A가 쓴 설명';upd(nd('c'));sv()");B.evaluate("nd('c').col='#00BF40';upd(nd('c'));sv()");settle(A,2000)
    c_a=[x for x in local(A)['n'] if x[0]=='c'][0][1]
    ok('T4 같은 인물의 다른 필드 동시 수정이 모두 살아남음',c_a.get('desc')=='A가 쓴 설명' and c_a.get('col')=='#00BF40' and same(A,B,room=room))
    # T5 같은 필드 동시 수정 → 수렴
    A.evaluate("nd('c').name='이름-A';upd(nd('c'));sv()");B.evaluate("nd('c').name='이름-B';upd(nd('c'));sv()");settle(A,2000)
    ok('T5 같은 필드 동시 수정도 A·B·DB가 같은 값으로 수렴',same(A,B,room=room))
    # T6 삭제 → 연결선까지 → 실행 취소/다시 실행
    n0=len(local(A)['n']);l0=len(local(A)['l'])
    A.click('.p[data-id="d"] .im');A.keyboard.press('Delete');settle(A)
    ok('T6a 삭제가 B·DB 에 반영(인물·선)',same(A,B,room=room) and len(local(B)['n'])==n0-1 and len(local(B)['l'])<l0)
    A.click('#bun');settle(A)
    ok('T6b 실행 취소 → 인물과 선이 모두 복원(A·B·DB)',same(A,B,room=room) and len(local(B)['n'])==n0 and len(local(B)['l'])==l0)
    A.click('#bre');settle(A)
    ok('T6c 다시 실행 → 다시 삭제',same(A,B,room=room) and len(local(B)['n'])==n0-1)
    A.click('#bun');settle(A)
    # T7 내 실행 취소는 남의 편집을 건드리지 않음
    pb=[x for x in local(A)['n'] if x[0]=='b'][0][1]
    box=A.locator('.p[data-id="b"] .im').bounding_box();A.mouse.move(box['x']+40,box['y']+40);A.mouse.down();A.mouse.move(box['x']+150,box['y']-40,steps=10);A.mouse.up();settle(A)
    B.evaluate("nd('c').name='B가 바꾼 이름';upd(nd('c'));sv()");settle(B,1200)
    A.click('#bun');settle(A)
    pb2=[x for x in local(A)['n'] if x[0]=='b'][0][1]; cname=[x for x in local(A)['n'] if x[0]=='c'][0][1]['name']
    ok('T7 A가 되돌려도 B의 이름 변경은 유지, B 화면도 동일',(pb2['x'],pb2['y'])==(pb['x'],pb['y']) and cname=='B가 바꾼 이름' and same(A,B,room=room))
    # T8 입력 묶음
    A.click('.p[data-id="c"] .im');A.fill('#ins input[type=text]','');A.type('#ins input[type=text]','abcdef',delay=70);A.click('#cv',position={'x':200,'y':660});settle(A,1500)
    nm=lambda pg:[x for x in local(pg)['n'] if x[0]=='c'][0][1]['name']
    after=nm(A);A.click('#bun');settle(A)
    ok('T8 여러 글자 입력이 취소 한 번으로 되돌아감',after=='abcdef' and nm(A)=='B가 바꾼 이름' and nm(B)=='B가 바꾼 이름')
    # T9 지연(느린 네트워크) + 동시 편집
    A.evaluate("window.__rpcDelay=500")
    for i in range(3): A.evaluate(f"nd('b').x={100+i*30};upd(nd('b'));sv()");A.wait_for_timeout(120)
    B.evaluate("nd('b').y=-300;nd('b').name='B-late';upd(nd('b'));sv()");A.evaluate("nd('b').name='A-late';upd(nd('b'));sv()");settle(A,3500)
    A.evaluate("window.__rpcDelay=0");settle(A,1200)
    ok('T9 느린 전송 + 동시 편집에서도 A·B·DB 수렴',same(A,B,room=room))
    # T10 커서·접속자
    A.mouse.move(500,300);A.mouse.move(700,420,steps=6);settle(B,800)
    ok('T10 B에서 A의 커서와 접속자 2명이 보임',B.locator('.rc').count()==1 and B.locator('#pp .pc').count()==2 and B.eval_on_selector('.rc','e=>e.style.opacity')=='1')
    A.evaluate("select('c')");settle(B,600)
    ok('T10b A가 선택한 인물에 B 화면 링 표시',B.eval_on_selector('.n[data-id="c"]','e=>e.classList.contains("rs")'))
    # T11 이벤트 유실 → 재접속 시 다시 맞춤
    key=B.evaluate('myKey');api('/ctl',{'drop':{key:True}})
    A.evaluate("nd('c').desc='유실 구간에 바뀐 설명';upd(nd('c'));sv()");settle(A,1500)
    lost=not same(A,B,room=room)
    api('/ctl',{'drop':{}});B.evaluate('window.__sbDrop(300)');settle(B,2500)
    ok('T11 이벤트를 놓쳤다가(유실 확인) 재접속하면 다시 같아짐',lost and same(A,B,room=room))
    # T12 영속성: 모두 나간 뒤 새 접속자 (자기 로컬 문서는 다른 내용)
    A.click('#bx');settle(A,800);B.click('#bx');settle(B,800)
    pre="try{localStorage.setItem('relmap_v1',JSON.stringify({view:null,nodes:[{id:'zzz',t:'p',x:0,y:0,name:'내 로컬 문서',desc:'',img:'',col:'#0066FF'}],links:[]}))}catch(e){}"
    C=client(b,pre);C.goto(URL+h);settle(C,2000)
    ok('T12 새 접속자는 DB 에 저장된 문서를 받고 자기 로컬 문서가 방을 덮어쓰지 않음',same(C,room=room) and not any(x[0]=='zzz' for x in local(C)['n']) and not any(r['id']=='zzz' for r in api('/dump?room='+room)['data']))
    ok('T14 방 안에서는 로컬 저장본을 건드리지 않음',json.loads(C.evaluate("localStorage.getItem('relmap_v1')"))['nodes'][0]['id']=='zzz')
    print('errors/dialogs:',ERR[:5]); b.close()
