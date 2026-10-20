"""Real click/resize regression for the common home-based header."""
import asyncio,os
from playwright.async_api import async_playwright
BASE=os.environ.get('BOOK_TEST_URL','http://127.0.0.1:4173')
ROUTES=['','adventurers','guilds','world','updates','events','chronicle','favorites','live','admin']
EXPECTED=['#/','#/adventurers','#/guilds','#/world','#/updates','#/events','#/chronicle','#/favorites','#/live']
async def run():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=await b.new_page()
  for w,h in [(1920,1080),(1536,864),(1366,768),(1100,650),(1099,800),(1024,768),(1001,700),(768,1024),(390,844),(320,568)]:
   await p.set_viewport_size({'width':w,'height':h});reference=None
   for route in ROUTES:
    await p.goto(BASE+'/#/'+route);await p.wait_for_timeout(30)
    assert await p.locator('.header .links a').evaluate_all('(nodes)=>nodes.map(n=>n.getAttribute("href"))')==EXPECTED,(w,route,'Menu order')
    logo=await p.locator('.logo').bounding_box();assert abs(logo['width']/logo['height']-240/155)<.005,(w,route,'Distorted logo')
    assert not await p.evaluate('document.documentElement.scrollWidth>innerWidth'),(w,route,'Horizontal overflow')
    if w<1100:
     bgm=await p.locator('.header .bgmPlayer').bounding_box();assert logo['x']+logo['width']<=bgm['x']+1,(w,route,'Logo overlaps controls')
     await p.locator('.menu').click();assert await p.locator('.menu').get_attribute('aria-expanded')=='true'
    header=await p.locator('.header').bounding_box();links=await p.locator('.links').bounding_box()
    relative=[round((links['x']-header['x'])/header['width'],3),round((links['y']-header['y'])/header['height'],3)]
    if route!='admin':
     if reference is None:reference=relative
     assert relative==reference,(w,route,'Different menu position',relative,reference)
    target=p.locator('.header a[href="#/events"]');r=await target.bounding_box();assert r['height']>=44
    await p.mouse.click(r['x']+r['width']/2,r['y']+r['height']/2);await p.wait_for_timeout(40)
    assert await p.evaluate('location.hash')=='#/events',(w,route,'Click failed')
   # Resizing the same page must switch menu modes without stale inline state.
   await p.goto(BASE+'/#/');await p.set_viewport_size({'width':1001,'height':700});await p.locator('.menu').click();await p.locator('.links a').last.focus();await p.keyboard.press('Escape');assert not await p.locator('.links').is_visible()
  await b.close()
 print('PASS: 10 routes × 10 screen sizes; same nine menu items and positions; proportional logo; no overlap/overflow; real event-menu clicks; tablet breakpoint and Escape close.')
asyncio.run(run())
