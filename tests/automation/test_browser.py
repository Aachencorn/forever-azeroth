"""Mock reports/public snapshots only. No SOOP network or real video analysis."""
import asyncio,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from test_engine import fixture,obs,NOW
BASE=os.environ.get('BOOK_TEST_URL','http://127.0.0.1:4173')
async def run():
 from playwright.async_api import async_playwright
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE+'/#/admin');await page.get_by_role('button',name='방송 자동 분석',exact=True).click();await page.wait_for_timeout(100)
  assert await page.get_by_text('아직 실제 분석 보고서가 없습니다.',exact=True).count()==1
  assert '미측정' in await page.locator('#adminContent').inner_text()
  original=await page.evaluate('JSON.stringify(data)')
  s=fixture();j=s.reserve(NOW)[0];s.complete(j['id'],obs(j,guild='새길드'),NOW+30);report=s.dashboard(NOW+30)
  await page.locator('#adminContent input[type=file]').set_input_files({'name':'review.json','mimeType':'application/json','buffer':json.dumps(report).encode()})
  await page.get_by_role('button',name='승인 요청',exact=True).click();await page.get_by_role('button',name='비활성화 요청',exact=True).click()
  async with page.expect_download() as download:await page.get_by_role('button',name='승인·거절·복원 요청 다운로드 (2)',exact=True).click()
  file=await (await download.value).path();decisions=json.loads(Path(file).read_text());assert len(decisions)==2 and decisions[0]['decision']=='approve' and decisions[1]['enabled'] is False
  assert await page.evaluate('JSON.stringify(data)')==original
  for width in [3440,1536,1024,768,390,320]:
   await page.set_viewport_size({'width':width,'height':1000});assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth'),width
  # Public loader is opt-in; local favorites and reports are retained, storage is not rewritten.
  await page.evaluate("localStorage.setItem('fa-favs',JSON.stringify({people:['wak'],guilds:[]}));data.people[0].characters[0].level='20';data.people[0].image='https://example.com/manual.jpg';data.reports=[{id:'private'}];save()")
  saved=await page.evaluate('localStorage.getItem(KEY)')
  remote=await page.evaluate('structuredClone(data)');remote['people'][0]['characters'][0]['level']='21';remote['people'][0]['image']='';remote.pop('reports')
  await page.route('**/data/publication-manifest.json',lambda r:r.fulfill(json={'schema':'wapobook-publication-manifest-v1','enabled':True,'source':'data/published-archive.json'}))
  await page.route('**/data/published-archive.json',lambda r:r.fulfill(json={'schema':'wapobook-public-archive-v1','revision':'test-only','archive':remote,'dashboard':report}))
  await page.evaluate('loadPublishedArchive()')
  assert await page.evaluate('data.people[0].characters[0].level')=='21'
  assert await page.evaluate('data.people[0].image')=='https://example.com/manual.jpg'
  assert await page.evaluate('data.reports[0].id')=='private'
  assert await page.evaluate('localStorage.getItem(KEY)')==saved
  assert await page.evaluate("JSON.parse(localStorage.getItem('fa-favs')).people[0]")=='wak'
  assert not errors,errors
  await browser.close();print('PASS: inactive dashboard, review/toggle downloads, no unauthorized browser writes, six widths, opt-in public overlay and local data preservation')
if __name__=='__main__':asyncio.run(run())
