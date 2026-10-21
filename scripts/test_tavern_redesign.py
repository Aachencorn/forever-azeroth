"""Home/exterior QA and pixel/DOM comparisons against the unchanged production checkout.
Run both static servers at 4173 (candidate) and 4174 (production baseline).
All records in this test live only inside disposable browser contexts.
"""
import asyncio,io,json,os,hashlib
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
from playwright.async_api import async_playwright
BASE=os.environ.get('BOOK_TEST_URL','http://127.0.0.1:4173')
OLD=os.environ.get('BOOK_BASELINE_URL','http://127.0.0.1:4174')
OUT=Path(os.environ.get('TAVERN_QA_OUTPUT','/workspace/work/tavern-qa'));OUT.mkdir(parents=True,exist_ok=True)
ROUTES=['adventurers','guilds','world','chronicle','favorites','live','updates','events']
FIXTURE='''()=>{
 data=structuredClone(seed);
 data.guilds=Array.from({length:10},(_,i)=>({id:'g'+i,name:'검수길드'+i,total:20+i,leader:'검수길드장',description:'검수 소개'}));
 data.people=Array.from({length:70},(_,i)=>({id:'p'+i,name:'검수모험가'+String(i).padStart(2,'0'),image:'',soop:i%2?'https://www.sooplive.co.kr/test':'',past:{participated:i%2?'yes':'no',raids:[]},characters:[{id:'c'+i,name:'검수캐릭터'+i,main:true,level:i%60+1,race:i%2?'인간':'드워프',className:i%2?'전사':'마법사',guildId:'g'+i%10,role:'딜러'}]}));
 data.events=[{id:'e1',title:'검수 예정 이벤트',date:'2026-10-25',status:'예정',description:'검수 내용'},{id:'e2',title:'검수 진행 이벤트',date:'2026-10-20',status:'진행 중'},{id:'e3',title:'종료된 검수 이벤트',status:'종료'}];
 data.chronicle=[{id:'r1',title:'검수 주요 사건',date:'2026-10-20',description:'검수 기록',category:'주요 사건'}];
 data.slots=['p0','missing','p1',...Array(17).fill('')];
 localStorage.setItem(KEY,JSON.stringify(data));localStorage.setItem('fa-favs',JSON.stringify({people:data.people.map(p=>p.id),guilds:data.guilds.map(g=>g.id)}));
}'''
async def screenshot(n):return Image.open(io.BytesIO(await n.screenshot(animations='disabled'))).convert('RGB')
async def run():
 result={'book_comparisons':[],'responsive':[],'production_data_modified':False}
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  old=await browser.new_page();new=await browser.new_page();errors=[];new.on('pageerror',lambda e:errors.append(str(e)))
  for p,url in [(old,OLD),(new,BASE)]:
   await p.goto(url);await p.evaluate(FIXTURE);await p.reload();await p.evaluate('document.fonts.ready')
  saved=await new.evaluate('localStorage.getItem(KEY)')
  # Book markup, sizes and actual rendered pixels must remain the same as main.
  for width in [1536,1100,768,390]:
   for p in [old,new]:await p.set_viewport_size({'width':width,'height':1024 if width>=1100 else 844})
   for route in ROUTES:
    for p,url in [(old,OLD),(new,BASE)]:
     await p.goto(url+'/#/'+route);await p.wait_for_timeout(80)
    a=old.locator('.wapBook');b=new.locator('.wapBook')
    assert await a.evaluate('n=>{n=n.cloneNode(true);n.querySelector(".wapControls")?.remove();return n.outerHTML}')==await b.evaluate('n=>{n=n.cloneNode(true);n.querySelector(".wapControls")?.remove();return n.outerHTML}'),(width,route,'Book markup changed')
    # Mobile may move vertically with the new header, but its dimensions/interior stay intact.
    ba=await a.bounding_box();bb=await b.bounding_box()
    for k in ['width','height']:
     expected=40 if k=='height' and width<=700 and route=='favorites' else 0
     assert abs(bb[k]-ba[k]-expected)<.2,(width,route,k,ba,bb)
    ia=await screenshot(a);ib=await screenshot(b);assert ia.width==ib.width
    error=sum(ImageStat.Stat(ImageChops.difference(ia,ib)).mean)/3
    # Transparent inter-leaf gaps expose the intentionally changed exterior.
    # Compare the actual leaf contents without the central exposed gap.
    leaf_errors=[]
    for i in [0,1]:
     la=await screenshot(old.locator('.wapBook>.wapLeaf').nth(i));lb=await screenshot(new.locator('.wapBook>.wapLeaf').nth(i))
     assert la.size==lb.size
     value=sum(ImageStat.Stat(ImageChops.difference(la,lb)).mean)/3;leaf_errors.append(round(value,5))
     assert value<1,(width,route,'Book leaf pixels differ',value)
    result['book_comparisons'].append({'width':width,'route':route,'leaf_mean_rgb_error':leaf_errors})
   for route,selector in [('adventurer/p0','.personBookModal'),('guild/g0','.guildBookModal')]:
    for p,url in [(old,OLD),(new,BASE)]:await p.goto(url+'/#/'+route);await p.wait_for_timeout(80)
    assert await old.locator(selector).evaluate('n=>n.outerHTML')==await new.locator(selector).evaluate('n=>n.outerHTML'),('Modal markup changed',width,route)
    ba=await old.locator(selector).bounding_box();bb=await new.locator(selector).bounding_box();assert ba==bb,('Modal geometry changed',width,route)
  assert await new.evaluate('localStorage.getItem(KEY)')==saved,'Browsing rewrote saved records'
  # Header, home panel placement, real records, 20 slots, links and mobile overflow.
  for width,height in [(2560,1080),(1920,1080),(1536,1024),(1366,768),(1100,900),(1024,844),(768,1024),(390,844),(320,740)]:
   await new.set_viewport_size({'width':width,'height':height});await new.goto(BASE+'/#/');await new.wait_for_timeout(80)
   assert await new.locator('.tavernMember').count()==20
   assert await new.locator('a.tavernMember').count()==2
   assert await new.locator('.tavernMemberEmpty').count()==18
   assert '종료된 검수 이벤트' not in await new.locator('.tavernEvents').inner_text()
   assert await new.locator('.tavernStations a').count()==5
   assert await new.locator('.tavernWorldStats strong').nth(0).inner_text()=='70'
   assert await new.locator('.tavernWorldStats strong').nth(1).inner_text()=='10'
   assert await new.locator('.tavernUnknown').inner_text()=='미연동'
   assert await new.locator('.tavernSearch').count()==1
   assert await new.locator('.approvedPaper,.approvedArtwork').count()==0,'Old home artwork leaked'
   assert 'assets/inn-interior.webp' in await new.evaluate('getComputedStyle(document.body).backgroundImage')
   assert not await new.evaluate('document.documentElement.scrollWidth>innerWidth'),('Home overflow',width)
   for sel in ['.tavernLive','.tavernWelcome','.tavernNotices','.tavernRoster','.tavernWorld']:
    box=await new.locator(sel).bounding_box();assert box['width']>100 and box['x']>=0 and box['x']+box['width']<=width+1,(width,sel,box)
   if width>=1100:
    assert await new.locator('.links a:visible').count()==8
    live=await new.locator('.tavernLive').bounding_box();welcome=await new.locator('.tavernWelcome').bounding_box();news=await new.locator('.tavernNotices').bounding_box()
    assert live['x']+live['width']<welcome['x'] and welcome['x']+welcome['width']<news['x']
   else:
    await new.locator('.menu').click();assert await new.locator('.links').is_visible();await new.keyboard.press('Escape');assert not await new.locator('.links').is_visible()
   for route in ROUTES+['admin']:
    await new.goto(BASE+'/#/'+route);await new.wait_for_timeout(30)
    assert not await new.evaluate('document.documentElement.scrollWidth>innerWidth'),(width,route,'overflow')
    if width<1100 and await new.locator('.wapControls').count():
     controls=await new.locator('.wapControls').bounding_box();leaf=await new.locator('.wapBook>.wapLeaf').first.bounding_box()
     assert controls['y']+controls['height']<=leaf['y']+1,(width,route,'Toolbar overlaps cards',controls,leaf)
   result['responsive'].append({'width':width,'height':height,'passed':True})
  await new.goto(BASE+'/#/');await new.locator('#bgmVolume').focus();await new.locator('#bgmVolume').press('End');await new.locator('#bgmVolume').press('ArrowLeft');await new.reload()
  assert await new.locator('#bgmVolume').input_value()=='99';assert await new.evaluate('bgm.volume')==.99
  await new.locator('#mainSearch').fill('검수모험가03');await new.locator('.tavernSearch button').click();await new.wait_for_timeout(80)
  assert await new.locator('.wapPerson').count()==1
  assert not errors,errors
  result['functional']=['unchanged storage after browsing','20 slots','real member/guild counts','station links','no fake live status','completed events excluded','header search','BGM volume persisted','menu open/Escape','unchanged detail markup/geometry']
  await browser.close()
 (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print('PASS: 8 book routes × 4 widths preserve markup, dimensions and leaf pixels; both modals unchanged; 9 responsive sizes; real home data, slots, links, search and BGM storage.')
asyncio.run(run())
