"""Synthetic image transport test, not a SOOP connectivity test."""
import asyncio,io,os
from PIL import Image
from playwright.async_api import async_playwright
async def run():
 out=io.BytesIO();Image.new('RGB',(4,4),'blue').save(out,format='PNG');png=out.getvalue();seen=[]
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page()
  async def route(r):seen.append(r.request.url);await r.fulfill(status=200,content_type='image/png',body=png)
  await page.route('https://profile.img.sooplive.co.kr/**',route)
  await page.goto(os.environ.get('BOOK_TEST_URL','http://127.0.0.1:4173')+'/#/admin')
  await page.evaluate("""data.people=[{id:'off',name:'오프라인 검증',soop:'ecvhao',image:'',characters:[],status:'streamend'},{id:'on',name:'온라인 검증',soop:'neez0611',image:'',characters:[],status:'streaming'},{id:'keep',name:'기존 사진',soop:'mygomiee',image:'https://example.com/manual.jpg',characters:[]}];save();""")
  await page.get_by_role('button',name='엑셀 일괄 등록',exact=True).click()
  await page.get_by_role('button',name='ID로 프로필 사진 조회',exact=True).click()
  await page.wait_for_function('!adminImportBusy&&adminImportState?.next?.people?.[0]?.image',timeout=15000)
  assert await page.evaluate("adminImportState.results.filter(r=>r.status==='성공').length")==2
  assert await page.evaluate("data.people[0].image")==''
  assert not any('mygomiee' in u for u in seen)
  page.once('dialog',lambda d:d.accept())
  async with page.expect_download():await page.get_by_role('button',name='성공 항목 병합 승인',exact=True).click()
  assert await page.evaluate("data.people[0].image.endsWith('/ecvhao/ecvhao.jpg')")
  assert await page.evaluate("data.people[1].image.endsWith('/neez0611/neez0611.jpg')")
  assert await page.evaluate('data.people[2].image')=='https://example.com/manual.jpg'
  await page.reload();assert await page.evaluate("data.people[0].image.endsWith('/ecvhao/ecvhao.jpg')")
  await b.close()
  print('PASS: synthetic profile image loads for offline and online IDs, explicit approval, existing photo protection and persistence')
asyncio.run(run())
