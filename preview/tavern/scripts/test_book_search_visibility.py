"""Typing must visibly change the real search field, even over painted scenery."""
import asyncio,io,os
from PIL import Image,ImageChops
from playwright.async_api import async_playwright
BASE=os.environ.get('BOOK_TEST_URL','http://127.0.0.1:4173')
async def run():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=await b.new_page()
  for width in [1536,1100]:
   await p.set_viewport_size({'width':width,'height':1024})
   for route in ['adventurers','guilds','favorites','live']:
    await p.goto(BASE+'/#/'+route);field=p.locator('#bookSearch');await field.fill('');await p.wait_for_timeout(40)
    before=Image.open(io.BytesIO(await field.screenshot())).convert('RGB')
    await field.fill('검수 검색어');await p.wait_for_timeout(40)
    after=Image.open(io.BytesIO(await field.screenshot())).convert('RGB')
    changed=sum(max(pixel)>25 for pixel in ImageChops.difference(before,after).get_flattened_data())
    assert changed>80,(width,route,'Search text is covered by scenery',changed)
    assert await field.input_value()=='검수 검색어'
  for width in [1024,768,390,320]:
   await p.set_viewport_size({'width':width,'height':844});reference=None
   for route in ['','adventurers','guilds','world','updates','chronicle','favorites','live']:
    await p.goto(BASE+'/#/'+route);n=p.locator('.portalHome' if not route else '.wapBook').first
    styles=await n.evaluate('n=>{let c=getComputedStyle(n);return [c.borderImageSource,c.borderImageSlice,c.borderTopWidth,c.backgroundImage]}')
    if reference is None:reference=styles
    assert styles==reference,(width,route,'Mobile frame differs from home',styles,reference)
  await b.close()
 print('PASS: actual typed search pixels visible on 4 routes × 2 widths; all 8 mobile books share frame and parchment at 4 widths.')
asyncio.run(run())
