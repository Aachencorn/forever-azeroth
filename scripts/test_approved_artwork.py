"""Compare original decorative pixels and measured layout against approved PNGs.
APPROVED_SOURCE_DIR must point to the user's ten originals (not shipped as records).
"""
import asyncio,io,json,os
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('APPROVED_SOURCE_DIR','/workspace/work/design'))
BASE=os.environ.get('BOOK_TEST_URL','http://127.0.0.1:4173')
async def run():
 manifest=json.loads((ROOT/'assets/approved/manifest.json').read_text())
 for key,item in manifest.items():
  original=Image.open(SOURCE/item['source']).convert('RGB');asset=Image.open(ROOT/f'assets/approved/{key}.webp').convert('RGB')
  assert original.size==asset.size and ImageChops.difference(original,asset).getbbox() is None,('Changed original pixels',key)
 home_header=Image.open(SOURCE/manifest["home"]["source"]).convert("RGB").resize((1536,1024),Image.Resampling.BILINEAR)
 results=[]
 async with async_playwright() as pw:
  b=await pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=await b.new_page(viewport={'width':1536,'height':1024},device_scale_factor=1)
  for key,route in [('home',''),('adventurers','adventurers'),('guilds','guilds'),('world','world'),('news','updates'),('chronicle','chronicle'),('favorites','favorites'),('live','live')]:
   await p.goto(BASE+'/#/'+route)
   await p.evaluate('''async()=>{let i=new Image();i.src=getComputedStyle(document.querySelector('.approvedArtwork')).backgroundImage.slice(5,-2);await i.decode();await document.fonts.ready}''')
   await p.wait_for_timeout(50)
   shot=Image.open(io.BytesIO(await p.screenshot())).convert('RGB');original=Image.open(SOURCE/manifest[key]['source']).convert('RGB').resize((1536,1024),Image.Resampling.BILINEAR)
   regions={'common-header-frame':(330,0,1465,34),'binding':(0,128,60,1015),'right-frame':(1498,128,1536,980),'banner':(90,160,950,245) if key=='live' else (90,160,950,260) if key=='favorites' else (90,160,950,285) if key!='home' else (90,160,1460,310)}
   for label,rect in regions.items():
    expected=home_header if label in ["common-header-frame","binding"] else original
    diff=ImageChops.difference(expected.crop(rect),shot.crop(rect));error=sum(ImageStat.Stat(diff).mean)/3
    assert error<2.0,(key,label,error)
    results.append({'page':key,'area':label,'mean_absolute_rgb_error':round(error,4)})
  # Check reference coordinate alignment of real cards, with no mockup registration.
  await p.goto(BASE+'/#/adventurers');box=await p.locator('.wapPerson').first.bounding_box()
  assert abs(box['x']-124)<=1 and abs(box['y']-379)<=1
  assert abs(box['width']-146)<=4 and abs(box['height']-137)<=4
  await p.evaluate("data.guilds.push({id:'qa-guild',name:'검수 길드',total:0,description:''})")
  await p.goto(BASE+'/#/guilds');box=await p.locator('.wapGuild').first.bounding_box();assert abs(box['x']-124)<=1 and abs(box['y']-393)<=1
  await p.goto(BASE+'/#/adventurer/wak');box=await p.locator('[role="dialog"]').bounding_box()
  assert abs(box['x']-350)<=5 and abs(box['y']-200)<=5,(box,'person popup')
  await p.goto(BASE+'/#/guild/qa-guild');box=await p.locator('[role="dialog"]').bounding_box()
  assert abs(box['x']-212)<=6 and abs(box['y']-212)<=6,(box,'guild popup')
  await b.close()
 print(json.dumps({'lossless_originals':10,'decorative_comparisons':results,'layout':'card and both popup reference coordinates passed'},ensure_ascii=False,indent=2))
asyncio.run(run())
