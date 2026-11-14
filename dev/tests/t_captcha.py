import json
from playwright.sync_api import sync_playwright
import os, tempfile
HERE=os.path.dirname(os.path.abspath(__file__))
STUB=open(os.path.join(HERE,'..','stubs','client_stub_cap.js'),encoding='utf-8').read()
ROOT=os.path.abspath(os.path.join(HERE,'..','..'))
URL='http://localhost:8765/index.html?mode=edit'
TSJS="window.turnstile={render(el,o){window.__tsRendered=(window.__tsRendered||0)+1;window.__tsOpts=o;setTimeout(()=>{if(window.__tsFail)o['error-callback'](window.__tsFail);else o.callback('tok-123')},window.__tsDelay||150);return 'w1'},remove(){window.__tsRemoved=1},reset(){}};"
def fulfiller(body,ct='application/javascript'): return lambda r,req=None:r.fulfill(status=200,content_type=ct,body=body)
def mk(b,cfg,need=True,ts='ok',extra=''):
    ctx=b.new_context(viewport={'width':1280,'height':760})
    ctx.route('**/@supabase/supabase-js@2.118.0/+esm',fulfiller(STUB))
    if ts=='ok': ctx.route('https://challenges.cloudflare.com/**',fulfiller(TSJS))
    elif ts=='abort': ctx.route('https://challenges.cloudflare.com/**',lambda r,req=None:r.abort())
    if cfg=='missing': ctx.route('**/config.js',fulfiller(open(os.path.join(ROOT,'index.html'),encoding='utf-8').read(),'text/html'))   # SPA 폴백 흉내
    elif cfg is not None: ctx.route('**/config.js',fulfiller('window.RELMAP='+json.dumps(cfg)+';'))
    ctx.add_init_script(("window.__needCaptcha=true;" if need else "")+extra)
    pg=ctx.new_page();pg.dialogs=[];pg.errs=[];pg.on('dialog',lambda d,pg=pg:(pg.dialogs.append(d.message),d.accept()));pg.on('pageerror',lambda e,pg=pg:pg.errs.append(str(e)));return pg
ok=lambda n,v:print(('PASS ' if v else 'FAIL ')+n)
C={'SB_URL':'http://localhost:8790','SB_KEY':'sb_publishable_test','TS_KEY':'0xTESTKEY'}
with sync_playwright() as p:
    b=p.chromium.launch()
    # C1 캡차 필수 + 사이트 키 설정: 확인 후 증표가 로그인에 전달됨
    pg=mk(b,C,extra="window.__tsDelay=1200;");pg.goto(URL);pg.wait_for_timeout(500);pg.click('#bk');pg.wait_for_timeout(600)
    ok('C1a 확인 화면이 뜸(위젯 렌더됨)',pg.locator('#tsb').count()==1 and pg.evaluate('window.__tsRendered')==1 and pg.evaluate('window.__tsOpts.sitekey')=='0xTESTKEY')
    pg.screenshot(path=os.path.join(tempfile.gettempdir(),'captcha_overlay.png'))
    pg.wait_for_timeout(2500)
    ok('C1b 증표가 signInAnonymously 로 전달되고 방에 입장, 확인 화면은 사라짐',pg.evaluate('window.__signinArgs&&window.__signinArgs.options.captchaToken')=='tok-123' and pg.locator('#tsb').count()==0 and pg.evaluate('ready')is True and not pg.dialogs)
    # C3 같은 브라우저로 링크 다시 열기: 이미 로그인되어 있으면 캡차를 다시 하지 않음
    h=pg.evaluate('location.hash');pg.reload();pg.wait_for_timeout(2500)
    ok('C3 재접속(세션 있음)에서는 캡차 없이 바로 입장',pg.evaluate('window.__tsRendered||0')==0 and pg.evaluate('ready')is True)
    # C2 캡차 필수인데 사이트 키 없음
    q=mk(b,{'SB_URL':C['SB_URL'],'SB_KEY':C['SB_KEY'],'TS_KEY':''});q.goto(URL);q.wait_for_timeout(500);q.click('#bk');q.wait_for_timeout(1200)
    ok('C2 사이트 키 없이 캡차가 켜져 있으면 TS_KEY 안내',any('TS_KEY' in d for d in q.dialogs) and q.evaluate('room')is None)
    # C4 Turnstile 오류 110200(허용되지 않은 도메인)
    q=mk(b,C,extra="window.__tsFail='110200';");q.goto(URL);q.wait_for_timeout(500);q.click('#bk');q.wait_for_timeout(1500)
    ok('C4 도메인 미등록 오류 → Hostname 안내, 확인 화면 정리됨',any('Hostname' in d for d in q.dialogs) and q.locator('#tsb').count()==0 and q.evaluate('room')is None)
    # C4b 사이트 키 오류 1101xx
    q=mk(b,C,extra="window.__tsFail='110100';");q.goto(URL);q.wait_for_timeout(500);q.click('#bk');q.wait_for_timeout(1500)
    ok('C4b 사이트 키 오류 → TS_KEY 확인 안내',any('사이트 키가 올바르지' in d for d in q.dialogs))
    # C5 Turnstile 스크립트 로드 실패
    q=mk(b,C,ts='abort');q.goto(URL);q.wait_for_timeout(500);q.click('#bk');q.wait_for_timeout(1500)
    ok('C5 Turnstile 스크립트 차단/오프라인 → 안내',any('스크립트' in d for d in q.dialogs) and q.evaluate('room')is None)
    # C6 config.js 가 없을 때(호스팅이 index.html 로 대신 응답) 앱은 정상 시작
    q=mk(b,'missing',need=False);q.goto(URL);q.wait_for_timeout(900)
    ok('C6 config.js 가 없어도 앱이 정상 시작(인물 표시)',q.evaluate('S.nodes.length')>0 and q.locator('.n').count()>0)
    # C7 캡차 꺼진 프로젝트 + 키 없음: 기존 방식 그대로 동작
    q=mk(b,{'SB_URL':C['SB_URL'],'SB_KEY':C['SB_KEY'],'TS_KEY':''},need=False);q.goto(URL);q.wait_for_timeout(500);q.click('#bk');q.wait_for_timeout(2500)
    ok('C7 캡차가 꺼진 경우 기존대로 입장',q.evaluate('ready')is True and not q.dialogs and q.evaluate('window.__signinArgs')is None)
    # C8 config.js 값이 prompt 없이 사용됨 + 일반 편집기능 정상
    ok('C8 config.js 로 URL/키를 읽어 입력창 없이 시작',not pg.dialogs and not q.dialogs)
    b.close()
