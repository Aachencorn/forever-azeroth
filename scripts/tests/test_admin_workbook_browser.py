"""Disposable browser test; requires running site server, playwright and openpyxl."""
import asyncio,json,os,tempfile
from pathlib import Path
from openpyxl import load_workbook
ROOT=Path(__file__).resolve().parents[2]
QA=Path(os.environ.get("IMPORT_QA_DIR",tempfile.mkdtemp(prefix="wapobook-import-qa-")))
QA.mkdir(parents=True,exist_ok=True)
BASE=os.environ.get("BOOK_TEST_URL","http://127.0.0.1:4173")
def fixtures():
 w=load_workbook(ROOT/"downloads/wapobook-admin-template.xlsx")
 for i in range(180):w["모험가 정보"].append(["테스트"+str(i),"캐릭터"+str(i),i+1,"인간","전사","분노","딜러","테스트길드","https://www.sooplive.com/station/test"+str(i),"예"])
 w["길드 정보"].append(["테스트길드","길드장",180,"검증 전용 길드","2026-10-22"])
 w["이전 시즌 참여 기록"].append(["테스트0","참가",70,"전사","분노","카라잔"])
 w.save(QA/"import-180.xlsx")
 w["모험가 정보"]["A3"]="=1+1";w.save(QA/"import-formula.xlsx")

from playwright.async_api import async_playwright
async def run():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  p=await browser.new_page(viewport={'width':1440,'height':1000});errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
  await p.goto(BASE+'/#/admin')
  await p.get_by_role('button',name='엑셀 일괄 등록',exact=True).click()
  assert await p.get_by_role('link',name='엑셀 양식 다운로드').count()==1
  await p.get_by_role('button',name='사진 수동 등록·수정',exact=True).click()
  await p.locator('#editForm [name="personId"]').select_option('wak')
  await p.locator('#editForm [name="image"]').fill('https://example.com/manual.jpg')
  await p.get_by_role('button',name='저장하고 공개',exact=True).click()
  assert await p.evaluate('data.people[0].image')=='https://example.com/manual.jpg'
  await p.reload();await p.get_by_role('button',name='엑셀 일괄 등록',exact=True).click()
  assert await p.evaluate('data.people[0].image')=='https://example.com/manual.jpg'
  await p.evaluate("localStorage.setItem('fa-favs',JSON.stringify({people:['wak'],guilds:[]}));")
  before=await p.evaluate('JSON.stringify(data)')
  await p.locator('#adminWorkbook').set_input_files(str(QA/'import-180.xlsx'))
  await p.wait_for_function('adminImportState?.next?.people?.length===181',timeout=30000)
  assert await p.evaluate('JSON.stringify(data)')==before
  assert await p.locator('.importResults tbody tr').count()==182
  await p.screenshot(path=str(QA/'xlsx-import-desktop.png'),full_page=True)
  p.once('dialog',lambda d:d.accept())
  async with p.expect_download() as d:
   await p.get_by_role('button',name='성공 항목 병합 승인').click()
  await (await d.value).save_as(str(QA/'import-before-backup.json'))
  assert await p.evaluate('data.people.length')==181
  assert await p.evaluate('data.people[0].image')=='https://example.com/manual.jpg'
  assert await p.evaluate('data.guilds.length')==1
  assert await p.evaluate('data.people[1].past.participated')=='yes'
  assert json.loads(await p.evaluate("localStorage.getItem('fa-favs')"))['people']==['wak']
  async with p.expect_download() as d:await p.get_by_role('button',name='사진 조회 요청 JSON 다운로드').click()
  await (await d.value).save_as(str(QA/'requests-180.json'))
  assert len(json.load(open(str(QA/'requests-180.json')))['accounts'])==180
  snapshot=await p.evaluate('JSON.stringify(data)')
  async with p.expect_download() as d:await p.get_by_role('button',name='SOOP ID 조회 대상 다운로드',exact=True).click()
  await (await d.value).save_as(str(QA/'directory-180.json'))
  targets=json.loads((QA/'directory-180.json').read_text())
  assert len(targets['accounts'])==180
  assert all(r['requested']['nickname'] and r['requested']['live']['status'] for r in targets['accounts'])
  assert await p.evaluate('JSON.stringify(data)')==snapshot
  assert await p.get_by_role('button',name='성공 항목 병합 승인',exact=True).is_disabled()

  await p.reload();await p.get_by_role('button',name='엑셀 일괄 등록',exact=True).click()
  assert await p.evaluate('data.people.length')==181
  await p.locator('#adminWorkbook').set_input_files(str(QA/'import-180.xlsx'));await p.wait_for_function('adminImportState?.results?.length===182')
  assert await p.evaluate("adminImportState.results.every(r=>r.status==='중복')")
  await p.locator('#adminWorkbook').set_input_files(str(QA/'import-formula.xlsx'));await p.wait_for_function("adminImportState?.message?.includes('수식')")
  assert await p.evaluate('data.people.length')==181
  report={'schema':'wapobook-soop-profiles-v1','results':[{'accountId':'test0','status':'success','sourceType':'station-profile','imageUrl':'https://profile.img.sooplive.com/LOGO/te/test0/test0.jpg'},{'accountId':'test1','status':'no_image'}]}
  await p.locator('#adminProfiles').set_input_files({'name':'profiles.json','mimeType':'application/json','buffer':json.dumps(report).encode()})
  await p.wait_for_function('adminImportState?.results?.length===2')
  assert await p.evaluate("adminImportState.results.map(r=>r.status).join(',')")=='성공,이미지 없음'
  assert await p.evaluate('data.people[1].image')==''
  # Viewport checks, no mutation of actual website data.
  for width in [1440,1024,768,390,320]:
   await p.set_viewport_size({'width':width,'height':900});await p.wait_for_timeout(100)
   assert not await p.evaluate('document.documentElement.scrollWidth>innerWidth'),width
  await p.screenshot(path=str(QA/'xlsx-import-mobile.png'),full_page=True)
  await p.evaluate("location.hash='/adventurers'");await p.wait_for_timeout(200)
  assert await p.locator('#bookSearch').count()==1
  await p.locator('#bookSearch').fill('테스트179');await p.wait_for_timeout(150)
  assert await p.locator('.wapPerson').count()==1
  assert not errors,errors
  print('PASS: manual image UI/persistence/protection, browser XLSX 180 rows, preview/approval, backup, persistence, duplicates, formula rejection, request export, profile preview, search and five viewports')
  await browser.close()
fixtures()
asyncio.run(run())
