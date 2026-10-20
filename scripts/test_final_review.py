"""Final visual/functional regressions in a disposable browser only.
Use BOOK_TEST_URL for a running build; never writes fixtures to repository data.
"""
import asyncio, os
from playwright.async_api import async_playwright
BASE=os.environ.get('BOOK_TEST_URL','http://127.0.0.1:4173')
async def run():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  ctx=await b.new_context(viewport={'width':1536,'height':1024});p=await ctx.new_page();errors=[];failures=[]
  p.on('pageerror',lambda e:errors.append(str(e)))
  p.on('response',lambda r:failures.append(r.url) if r.status>=400 else None)
  await p.goto(BASE)
  await p.evaluate('''()=>{
   data=structuredClone(seed);data.guilds=Array.from({length:8},(_,i)=>({id:'g'+i,name:'검수길드'+i,total:20,description:'검수용 소개',leader:'검수 길드장'}));
   const jobs=['전사','성기사','사냥꾼','도적','사제','주술사','마법사','흑마법사','드루이드'];
   data.people=Array.from({length:96},(_,i)=>({id:'p'+i,name:'검수모험가'+String(i).padStart(2,'0'),image:i%2?'assets/wapobook/guild-banner.svg':'/qa-intentional-missing.png',soop:'',past:{participated:i%2?'yes':'no',raids:[]},characters:[{id:'c'+i,name:'검수캐릭터'+i,main:true,level:i%60+1,race:i%2?'인간':'드워프',className:jobs[i%9],guildId:'g'+i%8,role:['탱커','딜러','힐러'][i%3]}]}));
   localStorage.setItem(KEY,JSON.stringify(data));localStorage.setItem('fa-favs',JSON.stringify({people:data.people.map(p=>p.id),guilds:data.guilds.map(g=>g.id)}));
  }''');await p.reload()
  await p.goto(BASE+'/#/adventurers');await p.wait_for_timeout(50)
  await p.locator('#bookSearch').fill('검수');await p.locator('select[aria-label="종족"]').select_option('인간');await p.locator('#bookSort').select_option('level');await p.locator('[aria-label="다음 펼침"]:visible').first.click()
  state=await p.evaluate('JSON.stringify({bookIndex,bookQuery,bookSort,bookFilters})');await p.locator('.personLink').first.click();await p.wait_for_timeout(50)
  assert await p.locator('[role="dialog"]').count()==1
  await p.keyboard.press('Escape');await p.wait_for_timeout(50)
  assert await p.evaluate('JSON.stringify({bookIndex,bookQuery,bookSort,bookFilters})')==state,'Dialog reset list state'
  await p.goto(BASE+'/#/favorites');await p.wait_for_timeout(50)
  controls=await p.locator('.wapControls').bounding_box();card=await p.locator('.wapPerson').first.bounding_box();assert controls['y']+controls['height']<card['y'],'Favorites toolbar overlaps cards'
  await p.locator('#bookSearch').fill('없는검색어');assert '검색 조건' in await p.locator('.bookEmpty').first.inner_text()
  for width in [1536,1024,900,768,700,390,320]:
   await p.set_viewport_size({'width':width,'height':1024 if width==1536 else 844})
   for route in ['','adventurers','guilds','world','updates','chronicle','favorites','live','adventurer/p0','guild/g0']:
    await p.goto(BASE+'/#/'+route);await p.wait_for_timeout(60)
    assert not await p.evaluate('document.documentElement.scrollWidth>innerWidth'),(width,route)
    assert await p.evaluate('''()=>[...document.images].filter(i=>i.complete&&i.naturalWidth===0&&getComputedStyle(i).display!=='none'&&getComputedStyle(i).visibility!=='hidden'&&i.getBoundingClientRect().width>0&&i.getBoundingClientRect().height>0).length''')==0,('Visible broken image',width,route)
    if route=='world':
     assert await p.evaluate('''()=>[...document.querySelectorAll('.levelColumn>span')].every(n=>{let a=n.getBoundingClientRect(),b=n.closest('.wapLeaf').getBoundingClientRect();return a.bottom<=b.bottom+1})'''),('Level labels clipped',width)
    if route in ['adventurer/p0','guild/g0']:
     assert await p.locator('[role="dialog"]').count()==1
     assert await p.evaluate('''()=>{let n=document.querySelector('[role="dialog"]');return n.scrollWidth<=n.clientWidth+1}'''),('Modal horizontal scroll',width,route)
   if width<=1000:
    await p.goto(BASE+'/#/adventurers');await p.locator('.menu').click();assert await p.locator('.links').is_visible();await p.get_by_role('link',name='♜ 길드 도감',exact=True).click();await p.wait_for_timeout(40);assert await p.locator('h1').inner_text()=='길드 도감'
  # Click the painted desktop menu centers rather than navigating by URL.
  for width in [1536,1366,1100]:
   await p.set_viewport_size({'width':width,'height':1024})
   for href in ['#/adventurers','#/guilds','#/world','#/updates','#/chronicle','#/favorites','#/live','#/']:
    await p.goto(BASE+'/#/');await p.wait_for_timeout(30)
    a=p.locator('.header .links a[href="'+href+'"]')
    r=await a.bounding_box();assert r and r['height']>=44,('Collapsed menu hit target',width,href,r)
    await p.mouse.click(r['x']+r['width']/2,r['y']+r['height']/2)
    await p.wait_for_timeout(40);assert await p.evaluate('location.hash')==href,('Menu click failed',width,href)
  await p.set_viewport_size({'width':1536,'height':1024});await p.goto(BASE+'/#/admin');await p.wait_for_timeout(50)
  # Register records through the same forms used by an administrator.
  await p.get_by_role('button',name='+ 모험가 등록',exact=True).click();await p.locator('[name="name"]').fill('관리자 신규등록 검수');await p.get_by_role('button',name='저장하고 공개',exact=True).click()
  person=await p.evaluate("data.people.find(x=>x.name==='관리자 신규등록 검수').id")
  await p.reload();assert await p.evaluate("data.people.some(x=>x.name==='관리자 신규등록 검수')")
  await p.evaluate('(id)=>editPerson(id)',person);await p.locator('[name="name"]').fill('관리자 수정저장 검수');await p.get_by_role('button',name='저장하고 공개',exact=True).click();await p.reload();assert await p.evaluate("data.people.some(x=>x.name==='관리자 수정저장 검수')")
  for tab,button,values,collection in [
   ('길드','+ 길드 등록',{'name':'신규 길드 검수','total':'42'},'guilds'),
   ('이벤트','+ 이벤트 등록',{'title':'신규 이벤트 검수','description':'등록 저장 내용'},'events'),
   ('연대기','+ 주요 사건 등록',{'title':'신규 연대기 검수','date':'2026-10-20','description':'등록 저장 내용'},'chronicle')]:
   await p.locator('.adminSide').get_by_role('button',name=tab,exact=True).click();before=await p.evaluate(f'data.{collection}.length');await p.get_by_role('button',name=button,exact=True).click()
   for key,value in values.items():await p.locator(f'#editForm [name="{key}"]').fill(value)
   await p.get_by_role('button',name='저장하고 공개',exact=True).click();await p.reload();assert await p.evaluate(f'data.{collection}.length')==before+1
  assert not errors,errors
  assert all('/qa-intentional-missing.png' in url for url in failures),failures
  await ctx.close();await b.close()
  print('PASS: dialog list-state restoration; favorites overlap/empty search; 10 screens at 7 widths (320–1536); broken-image fallback; chart labels; modal width; desktop menu coordinate clicks at 3 widths; mobile menu; administrator person/guild/event/chronicle registration and durable edit/save; no unexpected HTTP failures or JS errors.')
asyncio.run(run())
