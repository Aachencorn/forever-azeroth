"""Isolated Chromium regression check; fixtures exist only in a disposable context.
Run after `python -m http.server 4173`: python scripts/test_book_ui.py
Requires Python playwright and Chromium. No fixtures are written to the archive.
"""
import asyncio, json, os
from playwright.async_api import async_playwright
BASE=os.environ.get('BOOK_TEST_URL','http://127.0.0.1:4173')
KEY='forever-azeroth-v1'
async def run():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  context=await browser.new_context(viewport={'width':1536,'height':1024})
  page=await context.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE);await page.wait_for_timeout(200)
  assert await page.evaluate('data.people.length')==1, 'No preview people may be seeded'
  assert await page.evaluate('data.guilds.length')==0
  assert await page.evaluate('localStorage.getItem("fa-example-data-20261015")') is None
  initial=await page.evaluate('JSON.stringify(data)')
  for route in ['adventurers','guilds','world','updates','events','chronicle','favorites','live','admin','report']:
   await page.goto(BASE+'/#/'+route);await page.wait_for_timeout(40)
   assert await page.locator('h1').count()>0,route
   assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth'),route
  assert await page.evaluate('JSON.stringify(data)')==initial
  fixture={'people':[], 'guilds':[], 'events':[{'id':'event-test','title':'검증 이벤트','date':'2026-10-20','status':'예정','description':'검증 상세','result':'검증 결과','source':'https://example.com/event'}], 'chronicle':[{'id':'chronicle-test','title':'검증 사건','date':'2026-10-20','category':'레이드','description':'검증 기록','guildId':'g0'}], 'reports':[], 'slots':['p0']+['']*19,'featuredEvent':'event-test','settings':{'siteName':'와포북'}}
  for i in range(10):fixture['guilds'].append({'id':f'g{i}','name':f'검증길드{i:02}','total':i*10,'leader':'검증 길드장','description':'검증용 소개'})
  for i in range(70):fixture['people'].append({'id':f'p{i}','name':f'검증모험가{i:02}','image':'','soop':'https://www.sooplive.co.kr/test' if i%2 else '', 'past':{'participated':'no' if i%2 else 'yes','level':20,'className':'전사','raids':['검증 레이드']}, 'characters':[{'id':f'c{i}','name':f'검증캐릭터{i:02}','main':True,'level':i+1,'race':'인간' if i%2 else '드워프','className':'전사' if i%2 else '마법사','role':'딜러','guildId':f'g{i%10}'}]})
  await page.evaluate('([k,v])=>localStorage.setItem(k,JSON.stringify(v))',[KEY,fixture]);await page.reload()
  stored=await page.evaluate('(k)=>localStorage.getItem(k)',KEY)
  await page.goto(BASE+'/#/adventurers');await page.wait_for_timeout(70)
  assert await page.locator('.wapPerson').count()==32
  await page.locator('button[aria-label="다음 펼침"]').first.click();assert await page.locator('.wapPerson').count()==32
  await page.locator('button[aria-label="다음 펼침"]').first.click();assert await page.locator('.wapPerson').count()==6
  assert await page.locator('button[aria-label="다음 펼침"]').first.is_disabled()
  await page.locator('#bookSearch').fill('검증모험가01');assert await page.locator('.wapPerson').count()==1
  await page.locator('#bookSearch').fill('검증');assert await page.locator('#bookSearch').input_value()=='검증'
  await page.locator('#bookSearch').press('End');await page.locator('#bookSearch').press('1');assert await page.locator('#bookSearch').input_value()=='검증1'
  await page.locator('#bookSearch').fill('');await page.locator('select[aria-label="직업"]').select_option('전사');assert await page.evaluate('filteredPeople().length')==35
  await page.locator('select[aria-label="종족"]').select_option('드워프');assert await page.locator('.wapPerson').count()==0
  await page.locator('select[aria-label="종족"]').select_option('');await page.locator('select[aria-label="직업"]').select_option('')
  await page.locator('#bookSort').select_option('level');assert await page.locator('.wapPerson strong').first.inner_text()=='검증모험가69'
  await page.locator('button[aria-label="목록 보기"]').click();assert await page.locator('.bookListView').count()==2
  await page.locator('button[aria-label="격자 보기"]').click()
  await page.locator('.cardFavorite').first.click();assert await page.evaluate('fav().people.length')==1
  await page.locator('.personLink').first.click();await page.wait_for_timeout(70);assert await page.locator('[role="dialog"]').count()==1
  await page.keyboard.press('Escape');await page.wait_for_timeout(70);assert await page.locator('[role="dialog"]').count()==0
  await page.goto(BASE+'/#/favorites');await page.wait_for_timeout(50);assert await page.locator('.wapPerson').count()==1
  await page.goto(BASE+'/#/guilds');await page.wait_for_timeout(50);assert await page.locator('.wapGuild').count()==8
  await page.locator('button[aria-label="다음 펼침"]').first.click();assert await page.locator('.wapGuild').count()==2
  await page.locator('.wapGuild>a').first.click();await page.wait_for_timeout(70);assert await page.locator('.guildBookModal').count()==1
  assert await page.locator('.wapMemberGrid a').count()==7
  await page.locator('.guildBookModal .heart').click();assert await page.evaluate('fav().guilds.length')==1
  await page.locator('.wapClose').click();await page.wait_for_timeout(70)
  await page.goto(BASE+'/#/live');await page.wait_for_timeout(50);assert await page.locator('.wapLiveCard').count()==16
  await page.locator('button[aria-label="다음 펼침"]').first.click();assert await page.locator('.wapLiveCard').count()==16
  assert await page.locator('.liveUnknown').first.inner_text()=='방송 상태 미연동'
  await page.goto(BASE+'/#/');await page.wait_for_timeout(50);await page.locator('#mainSearch').fill('검증모험가03');await page.locator('#mainSearch').press('Enter');await page.wait_for_timeout(70)
  assert await page.locator('.wapPerson').count()==1;assert await page.locator('#bookSearch').input_value()=='검증모험가03'
  await page.goto(BASE+'/#/updates');await page.wait_for_timeout(60);await page.get_by_role('button',name='이벤트',exact=True).click();assert '검증 이벤트' in await page.locator('.journalDetail').inner_text()
  await page.goto(BASE+'/#/event/event-test');await page.wait_for_timeout(50);assert '검증 결과' in await page.locator('.journalDetail').inner_text()
  await page.goto(BASE+'/#/chronicle');await page.wait_for_timeout(50);await page.get_by_role('button',name='레이드 기록',exact=True).click();assert '검증 사건' in await page.locator('.journalDetail').inner_text()
  assert await page.evaluate('(k)=>localStorage.getItem(k)',KEY)==stored,'Browsing changed archive data'
  await page.goto(BASE+'/#/admin');await page.wait_for_timeout(50);await page.get_by_role('button',name='수정',exact=True).first.click();await page.locator('input[name="name"]').fill('관리자 저장 검증');await page.get_by_role('button',name='저장하고 공개',exact=True).click();assert await page.evaluate('data.people[0].name')=='관리자 저장 검증'
  await page.reload();assert await page.evaluate('data.people[0].name')=='관리자 저장 검증'
  await page.get_by_role('button',name='+ 캐릭터',exact=True).first.click();await page.locator('input[name="name"]').fill('두번째 캐릭터');await page.get_by_role('button',name='저장하고 공개',exact=True).click();assert await page.evaluate('data.people[0].characters.length')==2
  await page.goto(BASE+'/#/adventurer/p0');await page.wait_for_timeout(50);assert '두번째 캐릭터' in await page.locator('[role="dialog"]').inner_text()
  for width in [390,768,1024]:
   await page.set_viewport_size({'width':width,'height':844})
   for route in ['','adventurers','guilds','world','updates','chronicle','favorites','live','adventurer/p1','guild/g1','admin']:
    await page.goto(BASE+'/#/'+route);await page.wait_for_timeout(35)
    assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth'),(width,route)
   if width==390:
    await page.goto(BASE+'/#/adventurers');await page.locator('.menu').click();assert await page.locator('.links').is_visible()
  assert not errors,errors
  await context.close();await browser.close()
  print('PASS: all routes; no example seeding; search focus; combined filters; sort; grid/list; spread boundaries; favorites; dialogs/Escape; main search; news/events/chronicle; admin persistence/characters; 390/768/1024 responsive; no JS errors.')
asyncio.run(run())
