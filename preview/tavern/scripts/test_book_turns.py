"""Book footers share geometry and retain real paging actions; fixtures stay in memory."""
import asyncio,os
from playwright.async_api import async_playwright
BASE=os.environ.get('BOOK_TEST_URL','http://127.0.0.1:4173')
async def run():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=await b.new_page()
  for width in [1536,1366,1100]:
   await p.set_viewport_size({'width':width,'height':1024});await p.goto(BASE)
   await p.evaluate('''()=>{
    data=structuredClone(seed);
    data.guilds=Array.from({length:12},(_,i)=>({id:'g'+i,name:'검수길드'+i,total:1}));
    data.people=Array.from({length:80},(_,i)=>({id:'p'+i,name:'검수모험가'+i,past:{participated:'yes',raids:[]},characters:[{id:'c'+i,name:'캐릭터'+i,level:40,className:'전사',guildId:'g'+i%12,main:true}]}));
    data.events=Array.from({length:13},(_,i)=>({id:'e'+i,title:'검수이벤트'+i,date:'2026-10-20',description:'검수 내용'}));
    data.chronicle=Array.from({length:13},(_,i)=>({id:'r'+i,title:'검수기록'+i,date:'2026-10-20',category:'주요 사건',description:'검수 내용'}));
    localStorage.setItem('fa-favs',JSON.stringify({people:data.people.map(x=>x.id),guilds:data.guilds.map(x=>x.id)}));
   }''')
   reference=None
   for route in ['adventurers','guilds','favorites','live','updates','events','chronicle']:
    await p.evaluate("()=>{bookIndex=0;journalPage=0;journalCategory='all'}")
    await p.goto(BASE+'/#/'+route);await p.wait_for_timeout(50)
    buttons=p.locator('.bookTurnBar button:visible');assert await buttons.count()==2,(route,'Two visible turn buttons required')
    boxes=[await buttons.nth(i).bounding_box() for i in [0,1]]
    if reference is None:reference=boxes
    assert all(abs(box[k]-reference[i][k])<.6 for i,box in enumerate(boxes) for k in ['x','y','width','height']),(width,route,boxes,reference)
    before=await p.locator('.bookTurnBar').inner_text();await buttons.nth(1).click();await p.wait_for_timeout(30)
    assert await p.locator('.bookTurnBar').inner_text()!=before,(route,'Counter did not change')
    state='journalPage' if route in ['updates','events','chronicle'] else 'bookIndex';assert await p.evaluate(state)==1,(route,'Next action failed')
    await p.locator('.bookTurnBar button:visible').first.click();assert await p.evaluate(state)==0,(route,'Previous action failed')
   await p.set_viewport_size({'width':390,'height':844});await p.goto(BASE+'/#/adventurers')
   assert not await p.locator('.bookTurnBar').is_visible()
   next_button=p.locator('.wapBook button[aria-label="다음 펼침"]:visible').first;await next_button.click();assert await p.evaluate('bookIndex')==1
  await b.close()
 print('PASS: 7 book routes × 3 widths share turn-button geometry; next/previous counters and actions work; mobile retains in-book controls.')
asyncio.run(run())
