"""Explicit public projection. Never publish administrator reports, tokens or raw frames."""
import copy

def project(archive):
 def fields(row,keys):return {k:copy.deepcopy(row[k]) for k in keys if k in row}
 out={}
 for key in ['slots','featuredEvent']:
  if key in archive:out[key]=copy.deepcopy(archive[key])
 out['settings']={'siteName':archive.get('settings',{}).get('siteName','와포북')}
 out['people']=[]
 for p in archive.get('people',[]):
  row=fields(p,['id','name','soop','image','returning','verified','race','className'])
  row['characters']=[]
  for c in p.get('characters',[]):
   char=fields(c,['id','name','level','race','className','spec','role','guildId','main'])
   char['guildHistory']=[fields(h,['guildId','recordedAt','changeId','restores']) for h in c.get('guildHistory',[])];row['characters'].append(char)
  row['past']=fields(p.get('past',{}),['participated','level','className','spec','raids']);out['people'].append(row)
 out['guilds']=[fields(g,['id','name','leader','total','description','verified','image']) for g in archive.get('guilds',[])]
 for key,keys in [('events',['id','title','date','status','description','result','source']),('chronicle',['id','title','date','category','description','source'])]:out[key]=[fields(r,keys) for r in archive.get(key,[])]
 return out

def public_dashboard(dashboard):
 out=copy.deepcopy(dashboard)
 out['changes']=[{k:v for k,v in c.items() if k in ['id','personId','characterId','field','before','after','status','observedAt','processedAt','automatic']} for c in out['changes'] if c['status'] in ['applied','restored']]
 return out
