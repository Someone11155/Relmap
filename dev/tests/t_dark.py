from helpers import *
import math,re
# 다크 모드: 사용자가 고른 색을 oklch 밝기 L 만 뒤집어 화면에 표시(저장값은 그대로). 검증용 색 변환은 앱 코드와 따로 여기서 계산.
BASE='http://localhost:8765/index.html'
EDIT=BASE+'?mode=edit'
def lin(v): return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def oklch(hexs):
    h=hexs.lstrip('#');h=''.join(c*2 for c in h) if len(h)<5 else h
    r,g,b=[lin(int(h[i:i+2],16)/255) for i in (0,2,4)]
    l=(.4122214708*r+.5363325363*g+.0514459929*b)**(1/3);m=(.2119034982*r+.6806995451*g+.1073969566*b)**(1/3);s=(.0883024619*r+.2817188376*g+.6299787005*b)**(1/3)
    L=.2104542553*l+.793617785*m-.0040720468*s;a=1.9779984951*l-2.428592205*m+.4505937099*s;bb=.0259040371*l+.7827717662*m-.808675766*s
    return L,math.hypot(a,bb),math.degrees(math.atan2(bb,a))%360
def rgb2hex(s):
    n=[int(x) for x in re.findall(r'\d+',s)[:3]];return '#%02x%02x%02x'%tuple(n)
def close(c,d):  # d 가 c 의 밝기만 뒤집은 색인지: L'≈1-L, 색상 같음, 채도는 늘지 않음
    L0,C0,H0=oklch(c);L1,C1,H1=oklch(d)
    dh=min(abs(H1-H0),360-abs(H1-H0))
    return abs(L1-(1-L0))<.03 and C1<=C0+.02 and (C0<.04 or C1<.02 or dh<4)
def mk(b,scheme):
    pg=b.new_context(viewport={'width':1280,'height':760},color_scheme=scheme).new_page();pg.on('pageerror',lambda e:ERR.append(str(e)));pg.on('dialog',lambda d:(ERR.append('DIALOG:'+d.message),d.accept()));return pg
bg=lambda pg,sel:rgb2hex(pg.eval_on_selector(sel,'e=>getComputedStyle(e).backgroundColor'))
SETUP="""()=>{S.nodes.filter(n=>n.t=='p').forEach((n,i)=>{n.col='#0066FF'});
 const g={id:'G9',t:'c',x:-300,y:300,w:200,h:200,title:'g',col:'#6541F2',op:8,m:[],ph:true},t={id:'T9',t:'t',x:-300,y:200,text:'글자',size:22,bold:false,col:'#171719'},u={id:'T8',t:'t',x:-300,y:150,text:'기본색',size:22,bold:false,col:''};
 S.nodes.push(g,t,u);mk(g);mk(t);mk(u);S.nodes.forEach(n=>{if(n.t!='w')upd(n)});lk('l1').col='#FF4242';
 nd('b').st=[['힘',7],['지능',9],['매력',5],['민첩',6],['체력',4],['의지',10]].map(([n,v])=>({n,v}));drawLinks();sv()}"""
dcs=lambda pg,c:pg.evaluate("c=>dc(c)",c)
with sync_playwright() as p:
    b=p.chromium.launch()
    L=mk(b,'light');L.goto(EDIT);settle(L,700);L.evaluate(SETUP);settle(L,200)
    ok('D1 라이트 모드: 고른 색 그대로 표시(인물 #0066FF)',bg(L,'.n.p[data-id="b"] .im')=='#0066ff' and dcs(L,'#0066FF')=='#0066FF')
    D=mk(b,'dark');D.goto(EDIT);settle(D,700);D.evaluate(SETUP);settle(D,200)
    cs=['#0066FF','#FF4242','#6541F2','#00BF40','#F0A000','#70737C','#171719','#F7F7F8','#FF00FF','#00FFFF','#FFE066']
    bad=[c for c in cs if not close(c,dcs(D,c))]
    ok('D2 다크 모드: 여러 색이 oklch 밝기만 뒤집힘(색상 유지, 밝기 L→1-L, 채도 안 늘어남)'+(' 어긋남:'+','.join(bad) if bad else ''),not bad)
    ok('D3 흰색↔검정 뒤집힘, 짧은 색(#f0a)·투명도 자리(#0066FF80) 처리, 이상한 값은 그대로',dcs(D,'#FFFFFF')=='#000000' and dcs(D,'#000000')=='#ffffff' and close('#ff00aa',dcs(D,'#f0a')) and dcs(D,'#0066FF80').endswith('80') and close('#0066FF',dcs(D,'#0066FF80')[:7]) and dcs(D,'red')=='red' and dcs(D,'')=='')
    e=lambda c:dcs(D,c)
    r=D.evaluate("""()=>({av:getComputedStyle(document.querySelector('.n.p[data-id="b"] .im')).backgroundColor,gb:getComputedStyle(els.G9).borderColor,tx:getComputedStyle(els.T9).color,tx0:els.T8.style.color,
      ln:[...document.querySelectorAll('svg line[stroke]')].map(x=>x.getAttribute('stroke')),pl:[...document.querySelectorAll('svg polygon[fill]')].map(x=>x.getAttribute('fill'))})""")
    D.evaluate("select('b')");settle(D,200);hx=D.eval_on_selector('#hxp polygon[fill]','e=>e.getAttribute("fill")')
    ok('D4 다크 모드: 인물·그룹 테두리·글자·관계선·육각형에 뒤집힌 색이 적용됨',rgb2hex(r['av'])==e('#0066FF').lower() and rgb2hex(r['gb'])==e('#6541F2').lower() and rgb2hex(r['tx'])==e('#171719').lower() and e('#FF4242') in r['ln'] and hx==e('#0066FF') and rgb2hex(r['av'])!='#0066ff')
    ok('D5 색을 안 정한 글자 상자는 그대로(테마 글자색 사용)',r['tx0']=='')
    ok('D6 저장값은 그대로(인물·그룹·선·글자 색, 파일 검증 왕복)',D.evaluate("[nd('b').col,nd('G9').col,nd('T9').col,lk('l1').col]")==['#0066FF','#6541F2','#171719','#FF4242'] and D.evaluate("cleanDoc(JSON.parse(JSON.stringify({nodes:S.nodes,links:S.links}))).nodes.find(n=>n.id=='b').col")=='#0066FF')
    D.evaluate("select(null)");D.evaluate("pfOpen('b')");settle(D,200)
    ok('D7 읽기 모드 프로필 모달의 색도 뒤집힘',D.evaluate("(()=>{const e=[...document.querySelectorAll('#pf [style*=background]')][0];return e?getComputedStyle(e).backgroundColor:''})()").replace(' ','')!='' and rgb2hex(D.evaluate("getComputedStyle([...document.querySelectorAll('#pf [style*=background]')][0]).backgroundColor"))==e('#0066FF').lower())
    D.evaluate("pfClose()")
    D.emulate_media(color_scheme='light');settle(D,300)
    ok('D8 화면 모드를 바꾸면 새로고침 없이 바로 원래 색으로 돌아옴',bg(D,'.n.p[data-id="b"] .im')=='#0066ff')
    D.emulate_media(color_scheme='dark');settle(D,300)
    ok('D9 다시 다크로 바꾸면 바로 뒤집힌 색으로 바뀜',bg(D,'.n.p[data-id="b"] .im')==e('#0066FF').lower())
    # ── 다크 모드의 색 선택칸: 화면에 칠해진 색을 보여 주고, 고른 색은 뒤집어 저장
    D.evaluate("select('b')");settle(D,200);pk=lambda:D.input_value('#ins [data-k=col]')
    ok('P1 다크 모드: 색 선택칸이 저장값(라이트 기준)이 아니라 화면에 칠해진 뒤집힌 색을 보여 줌',pk()==e('#0066FF').lower() and pk()!='#0066ff')
    D.fill('#ins [data-k=col]','#336699');settle(D,200)
    sh=bg(D,'.n.p[data-id="b"] .im');diff=max(abs(int(sh[i:i+2],16)-int('336699'[i-1:i+1],16)) for i in (1,3,5))
    ok('P2 다크 모드에서 고른 색은 뒤집어 저장되고, 화면에는 고른 색 그대로 보임',D.evaluate("nd('b').col")==e('#336699').lower() and diff<=4)
    D.emulate_media(color_scheme='light');settle(D,300)
    ok('P3 라이트로 바꾸면 선택칸이 저장값을 그대로 보여 줌',pk()==D.evaluate("nd('b').col") and bg(D,'.n.p[data-id="b"] .im')==D.evaluate("nd('b').col").lower())
    D.evaluate("select(null)")
    # ── 화면 모드 버튼(라이트·다크·시스템 설정)
    T=mk(b,'light');T.goto(EDIT);settle(T,700);T.evaluate(SETUP);settle(T,200)
    th=lambda:T.evaluate("document.documentElement.dataset.theme");bodyc=lambda:T.evaluate("getComputedStyle(document.body).backgroundColor");icon=lambda:T.get_attribute('#bth use','href');store=lambda:T.evaluate("localStorage.getItem('relmap_theme')")
    pick=lambda v:(T.click('#bth'),T.click(f'#dl [data-th={v}]'),settle(T,250))
    t0=[th(),icon(),'시스템 설정' in T.get_attribute('#bth','title')];T.click('#bth');settle(T,150)
    r=T.evaluate("(()=>{const d=document.querySelector('#dl').getBoundingClientRect(),b=document.querySelector('#bth').getBoundingClientRect();return [[...document.querySelectorAll('#dl [data-th]')].map(x=>x.textContent),[...document.querySelectorAll('#dl [data-th]')].map(x=>x.getAttribute('aria-pressed')),d.top>=b.bottom-1,d.left>=0,d.right<=innerWidth,d.bottom<=innerHeight]})()")
    ok('T1 화면 모드 버튼(처음엔 시스템 설정): 누르면 버튼 아래에 라이트·다크·시스템 설정 3가지가 뜨고 지금 모드가 표시됨, 화면 안에 들어옴',t0==['light','#i-monitor',True] and r==[['라이트','다크','시스템 설정'],['false','false','true'],True,True,True,True])
    T.click('#bth');pick('dark')
    ok('T2 다크를 고르면(시스템은 라이트) 바로 다크로 바뀜: 배경·인물 색 반전·아이콘·저장·메뉴 닫힘',th()=='dark' and bodyc()=='rgb(15, 15, 16)' and bg(T,'.n.p[data-id="b"] .im')==dcs(T,'#0066FF').lower() and bg(T,'.n.p[data-id="b"] .im')!='#0066ff' and icon()=='#i-moon' and store()=='dark' and not T.is_visible('#dl'))
    T.emulate_media(color_scheme='light');T.emulate_media(color_scheme='dark');T.emulate_media(color_scheme='light');settle(T,300)
    ok('T3 다크로 골라 두면 시스템 설정이 바뀌어도 그대로 다크',th()=='dark' and bodyc()=='rgb(15, 15, 16)')
    T.reload();settle(T,700)
    ok('T4 새로고침해도 고른 모드가 유지됨(첫 화면부터 다크)',th()=='dark' and bodyc()=='rgb(15, 15, 16)' and icon()=='#i-moon')
    T.emulate_media(color_scheme='dark');settle(T,200);T.evaluate(SETUP);settle(T,200);pick('light')
    ok('T5 라이트를 고르면(시스템은 다크) 라이트로: 배경·원래 색·아이콘',th()=='light' and bodyc()=='rgb(247, 247, 248)' and bg(T,'.n.p[data-id="b"] .im')=='#0066ff' and icon()=='#i-sun' and store()=='light')
    pick('system');ok0=[th(),icon(),store()]
    T.emulate_media(color_scheme='light');settle(T,250);a=th();T.emulate_media(color_scheme='dark');settle(T,250);c=th()
    ok('T6 시스템 설정을 고르면 시스템을 따라가고, 시스템이 바뀌면 바로 따라 바뀜',ok0==['dark','#i-monitor','system'] and a=='light' and c=='dark')
    T.evaluate("localStorage.setItem('relmap_theme','zzz')");T.reload();settle(T,700)
    ok('T7 저장된 값이 이상하면 무시하고 시스템 설정으로 시작',th()=='dark' and icon()=='#i-monitor')
    ok('Z 페이지 오류·예상 못한 대화상자 없음',not ERR)
    b.close()
