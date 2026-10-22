"""Offline policy/queue engine. No stream capture, OAuth, OCR, network or secrets.
Inputs must come from a separately authorized and calibrated provider.
"""
import copy,hashlib,json,re,math
from datetime import datetime,timezone
from urllib.parse import urlsplit

def stamp(value):
 if not isinstance(value,str):raise ValueError('timestamp_required')
 d=datetime.fromisoformat(value.replace('Z','+00:00'))
 if d.tzinfo is None:raise ValueError('timezone_required')
 return d.timestamp()
def iso(value):return datetime.fromtimestamp(value,timezone.utc).isoformat()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def account(url):
 value=str(url or '').strip().lower()
 if re.fullmatch(r'[a-z0-9_]{2,25}',value):return value
 u=urlsplit(value);m=re.fullmatch(r'/(?:station/)?([a-z0-9_]{2,25})(?:/.*)?',u.path)
 if u.scheme not in ['http','https'] or u.username or u.password or u.port or u.hostname not in ['www.sooplive.com','www.sooplive.co.kr','ch.sooplive.com','ch.sooplive.co.kr','bj.afreecatv.com'] or not m:raise ValueError('invalid_account')
 return m[1]
def primary(person):return next((c for c in person.get('characters',[]) if c.get('main')),None)
def new_state():return {'version':1,'targets':{},'statuses':{},'jobs':{},'changes':[],'decisions':[],'dailyCostUsd':{},'runErrors':[]}

class System:
 def __init__(self,archive,state,config):
  self.archive=copy.deepcopy(archive);self.state=copy.deepcopy(state);self.config=copy.deepcopy(config)
  if config['analysisIntervalSeconds']!=600:raise ValueError('interval_must_be_600_seconds')
  if not 1<=config['maxConcurrent']<=10:raise ValueError('invalid_concurrency')
 def person(self,pid):return next((p for p in self.archive.get('people',[]) if p['id']==pid),None)
 def gates(self):
  return [k for k in ['enabled','statusAccessVerified','videoAnalysisPermitted','realPilotPassed','migrationApproved'] if self.config.get(k) is not True]
 def set_enabled(self,pid,enabled,actor,now):
  if not self.person(pid) or type(enabled) is not bool or not actor:raise ValueError('invalid_target_decision')
  t=self.state['targets'].setdefault(pid,{})
  t['enabled']=enabled;self.state['decisions'].append({'type':'target_enabled','personId':pid,'enabled':enabled,'actor':actor,'at':iso(now)})
 def ingest_statuses(self,rows,now):
  if not self.config.get('statusAccessVerified'):raise ValueError('status_provider_unverified')
  groups={}
  for p in self.archive.get('people',[]):
   try:groups.setdefault(account(p.get('soop')),[]).append(p)
   except ValueError:continue
  seen=set()
  for row in rows:
   aid=row.get('accountId');matches=groups.get(aid,[])
   if len(matches)!=1:continue
   pid=matches[0]['id']
   if aid in seen:self.state['statuses'][pid]={'status':'unknown','error':'duplicate_status','checkedAt':iso(now)};continue
   seen.add(aid)
   try:
    at=stamp(row['checkedAt']);age=now-at
    if age<0 or age>self.config['statusFreshnessSeconds'] or row.get('status') not in ['streaming','streamend','unknown']:raise ValueError()
    status={k:copy.deepcopy(row.get(k)) for k in ['accountId','status','broadcastId','game','realm','classificationVerified','checkedAt']}
    # Exact realm classification must be provided by a verified source. Title keywords alone are insufficient.
    if status['status']=='streaming' and (not status['broadcastId'] or status['game']!='wow' or status['realm']!='forever' or status['classificationVerified'] is not True):status['error']='game_or_realm_unverified'
    self.state['statuses'][pid]=status
   except (ValueError,KeyError,TypeError):self.state['statuses'][pid]={'status':'unknown','error':'invalid_or_stale_status','checkedAt':iso(now)}
 def eligible(self,pid,now):
  p=self.person(pid);t=self.state['targets'].get(pid,{});s=self.state['statuses'].get(pid,{})
  if not p or t.get('enabled') is not True or not primary(p):return False
  try:
   aid=account(p.get('soop'));consent=self.config.get('approvedAccounts',{}).get(aid,{}).get('analysisAllowed') is True
   matches=[]
   for person in self.archive.get('people',[]):
    try:
     if account(person.get('soop'))==aid:matches.append(person)
    except ValueError:continue
   if len(matches)!=1 or s.get('accountId')!=aid:return False
  except ValueError:consent=False
  if not consent:return False
  try:fresh=0<=now-stamp(s.get('checkedAt'))<=self.config['statusFreshnessSeconds']
  except (ValueError,TypeError):return False
  return fresh and s.get('status')=='streaming' and not s.get('error') and s.get('game')=='wow' and s.get('realm')=='forever' and s.get('classificationVerified') is True
 def reserve(self,now):
  if self.gates():return []
  cfg=self.config;estimate=cfg.get('estimatedCostPerAnalysisUsd');budget=cfg.get('dailyBudgetUsd')
  if not isinstance(estimate,(int,float)) or isinstance(estimate,bool) or not math.isfinite(estimate) or estimate<=0 or not isinstance(budget,(int,float)) or isinstance(budget,bool) or not math.isfinite(budget) or budget<=0:return []
  # Expired leases are marked failed, not immediately retried. The 600-second cooldown remains.
  for j in self.state['jobs'].values():
   if j['status']=='running' and j['leaseUntil']<=now:
    j['status']='failed';j['error']='lease_expired';self.state['targets'][j['personId']]['error']='lease_expired'
    day=iso(j['startedAt'])[:10];self.state['dailyCostUsd'][day]=self.state['dailyCostUsd'].get(day,0)+j['reservedCostUsd'];j['costEstimated']=True
  active=[j for j in self.state['jobs'].values() if j['status']=='running'];capacity=max(0,cfg['maxConcurrent']-len(active));day=iso(now)[:10]
  pending_cost=sum(j['reservedCostUsd'] for j in active if iso(j['startedAt'])[:10]==day)
  spent=self.state['dailyCostUsd'].get(day,0);due=[]
  for p in self.archive.get('people',[]):
   pid=p['id'];t=self.state['targets'].get(pid,{})
   if self.eligible(pid,now) and not any(j['personId']==pid for j in active) and now>=t.get('nextDueAt',0):due.append((t.get('nextDueAt',0),pid))
  jobs=[]
  for _,pid in sorted(due):
   t=self.state['targets'][pid];t['queueSince']=t.get('queueSince',now)
   if not capacity or spent+pending_cost+estimate>budget:continue
   s=self.state['statuses'][pid];jid=digest([pid,s['broadcastId'],now,len(self.state['jobs'])])[:24]
   job={'id':jid,'personId':pid,'accountId':s['accountId'],'characterId':primary(self.person(pid))['id'],'broadcastId':s['broadcastId'],'status':'running','startedAt':now,'leaseUntil':now+cfg['leaseSeconds'],'reservedCostUsd':estimate,'characterFingerprint':digest({k:primary(self.person(pid)).get(k) for k in ['id','name','level','guildId']})}
   self.state['jobs'][jid]=job;t.update(lastAttemptAt=now,nextDueAt=now+600,error=None);t.pop('queueSince',None);jobs.append(copy.deepcopy(job));capacity-=1;pending_cost+=estimate
  return jobs
 def change(self,job,field,before,after,reason,confidence,frames,now):
  cid=digest([job['personId'],job['characterId'],field,before,after])[:24]
  # Pending/rejected/reverted identical evidence is never applied repeatedly.
  old=next((c for c in self.state['changes'] if c['id']==cid),None)
  if old:return old
  c={'id':cid,'personId':job['personId'],'characterId':job['characterId'],'field':field,'before':before,'after':after,'status':'pending','reason':reason,'confidence':confidence,'observedAt':iso(max((stamp(f['capturedAt']) for f in frames),default=now)),'recordedAt':iso(now),'jobId':job['id'],'evidence':[{'frameId':f['frameId'],'capturedAt':f['capturedAt'],'scene':f['scene'],'characterName':f.get('characterName'),'level':f.get('level'),'guildName':f.get('guildName'),'confidence':f.get('confidence'),'selfConfirmed':f.get('selfConfirmed')} for f in frames],'evidenceHash':digest(frames)}
  self.state['changes'].append(c);return c
 def apply(self,c,actor,now,automatic=False):
  p=self.person(c['personId']);char=primary(p) if p else None
  if not char or char['id']!=c['characterId']:raise ValueError('representative_changed')
  field=c['field']
  if field not in ['level','guildId']:raise ValueError('non_applicable_review')
  current=char.get(field,'');same=str(current)==str(c['before'])
  if not same:raise ValueError('stale_before_value')
  if field=='guildId':
   if automatic:raise ValueError('guild_requires_admin')
   if not any(g['id']==c['after'] for g in self.archive.get('guilds',[])):raise ValueError('guild_not_registered')
   history=char.setdefault('guildHistory',[]);history.append({'guildId':current,'recordedAt':iso(now),'changeId':c['id'],'actor':actor})
  char[field]=str(c['after']) if field=='level' else c['after'];c.update(status='applied',processedAt=iso(now),actor=actor,automatic=automatic)
 def complete(self,jid,observation,now):
  j=self.state['jobs'].get(jid)
  if not j:raise ValueError('unknown_job')
  if j['status']!='running':return 'duplicate_or_closed_job'
  if now>=j['leaseUntil']:
   j['status']='failed';j['error']='lease_expired';day=iso(j['startedAt'])[:10];self.state['dailyCostUsd'][day]=self.state['dailyCostUsd'].get(day,0)+j['reservedCostUsd'];j['costEstimated']=True;self.state['targets'][j['personId']]['error']='lease_expired';return 'lease_expired'
  t=self.state['targets'][j['personId']]
  cost=observation.get('actualCostUsd')
  if isinstance(cost,(int,float)) and not isinstance(cost,bool) and math.isfinite(cost) and cost>=0:
   day=iso(now)[:10];self.state['dailyCostUsd'][day]=self.state['dailyCostUsd'].get(day,0)+cost;j['actualCostUsd']=cost
  else:
   j['costEstimated']=True;t['error']='cost_unreported';day=iso(now)[:10];self.state['dailyCostUsd'][day]=self.state['dailyCostUsd'].get(day,0)+j['reservedCostUsd']
  j['status']='completed';j['completedAt']=now;t['lastAnalysisAt']=now
  # Turning off a target, ending a broadcast, a new representative, or provider failure prevents all writes.
  p=self.person(j['personId']);char=primary(p) if p else None
  if self.gates() or not self.eligible(j['personId'],now) or self.state['statuses'][j['personId']].get('broadcastId')!=j['broadcastId'] or self.state['statuses'][j['personId']].get('accountId')!=j['accountId'] or not char or char['id']!=j['characterId'] or observation.get('error'):
   t['error']='analysis_failed_or_target_changed';j['error']=t['error'];return 'preserved'
  if digest({k:char.get(k) for k in ['id','name','level','guildId']})!=j['characterFingerprint']:
   t['error']='archive_changed_since_reservation';return 'preserved'
  if observation.get('sourceType')!='authorized-live-sample':
   t['error']='non_live_or_unverified_source';return 'preserved'
  frames=observation.get('frames',[]);cfg=self.config
  if not isinstance(frames,list) or not cfg['minimumEvidenceFrames']<=len(frames)<=cfg['maximumEvidenceFrames']:
   t['error']='insufficient_evidence';return 'preserved'
  try:
   times=[stamp(f['capturedAt']) for f in frames]
   if len({f['frameId'] for f in frames})!=len(frames) or min(times)<j['startedAt'] or max(times)>now or max(times)-min(times)<cfg['minimumFrameSeparationSeconds']:raise ValueError()
   score=min(float(f['confidence']) for f in frames)
   if not 0<=score<=1 or any(not isinstance(f['confidence'],(float,int)) or isinstance(f['confidence'],bool) or not math.isfinite(float(f['confidence'])) or not 0<=float(f['confidence'])<=1 for f in frames):raise ValueError()
   if observation.get('accountId')!=j['accountId'] or observation.get('broadcastId')!=j['broadcastId']:raise ValueError()
   if any(f.get('characterName')!=char.get('name') or f.get('selfConfirmed') is not True or f.get('scene') not in ['self-character-sheet','self-guild-sheet','self-level-up'] for f in frames):
    self.change(j,'identity',char.get('name'),sorted({str(f.get('characterName','')) for f in frames}),'character_mismatch_or_ownership_unverified',score,frames,now);return 'review'
   if score<cfg['minimumConfidence']:
    self.change(j,'confidence',None,score,'low_confidence',score,frames,now);return 'review'
  except (KeyError,ValueError,TypeError,OverflowError):t['error']='invalid_evidence';return 'preserved'
  levels={str(f.get('level','')) for f in frames};guilds={str(f.get('guildName','')) for f in frames}
  if len(levels)==1:
   value=next(iter(levels));old=str(char.get('level',''))
   if value.isdigit() and old.isdigit() and 1<=int(value)<=999 and int(value)!=int(old):
    c=self.change(j,'level',old,str(int(value)),('verified_increase' if int(value)-int(old)<=cfg['maxAutomaticLevelIncrease'] else 'large_level_jump') if int(value)>int(old) else 'level_decrease',score,frames,now)
    if c['status']=='pending' and 0<int(value)-int(old)<=cfg['maxAutomaticLevelIncrease']:self.apply(c,'analysis-policy',now,True)
  elif any(levels):self.change(j,'inconsistent_level',char.get('level'),sorted(levels),'conflicting_frames',score,frames,now)
  if len(guilds)==1 and next(iter(guilds)):
   name=next(iter(guilds));matches=[g for g in self.archive.get('guilds',[]) if g['name']==name]
   if len(matches)==1 and matches[0]['id']!=char.get('guildId',''):self.change(j,'guildId',char.get('guildId',''),matches[0]['id'],'guild_requires_admin',score,frames,now)
   elif not matches:self.change(j,'unmapped_guild',char.get('guildId',''),name,'guild_not_registered',score,frames,now)
  elif len(guilds)>1:self.change(j,'inconsistent_guild',char.get('guildId',''),sorted(guilds),'conflicting_frames',score,frames,now)
  return 'processed'
 def decide(self,cid,decision,actor,now):
  c=next((c for c in self.state['changes'] if c['id']==cid),None)
  if not c or not actor or decision not in ['approve','reject','restore']:raise ValueError('invalid_decision')
  if decision=='restore':
   if c['status']!='applied':raise ValueError('not_applied')
   p=self.person(c['personId']);char=primary(p) if p else None
   if not char or char['id']!=c['characterId'] or str(char.get(c['field'],''))!=str(c['after']):raise ValueError('later_change_exists')
   if c['field']=='guildId':char.setdefault('guildHistory',[]).append({'guildId':char.get('guildId',''),'recordedAt':iso(now),'actor':actor,'restores':cid})
   char[c['field']]=c['before'];c.update(status='restored',restoredAt=iso(now),restoredBy=actor)
  else:
   if c['status']!='pending':raise ValueError('already_processed')
   if decision=='approve':self.apply(c,actor,now)
   else:c.update(status='rejected',processedAt=iso(now),actor=actor)
  self.state['decisions'].append({'changeId':cid,'decision':decision,'actor':actor,'at':iso(now)})
 def dashboard(self,now):
  rows=[]
  for p in self.archive.get('people',[]):
   t=self.state['targets'].get(p['id'],{});s=self.state['statuses'].get(p['id'],{})
   try:fresh=0<=now-stamp(s.get('checkedAt'))<=self.config['statusFreshnessSeconds']
   except (ValueError,TypeError):fresh=False
   rows.append({'personId':p['id'],'name':p['name'],'enabled':t.get('enabled',False),'status':s.get('status','unknown') if fresh else 'unknown','gameVerified':fresh and not s.get('error') and s.get('classificationVerified') is True,'lastAnalysisAt':iso(t['lastAnalysisAt']) if 'lastAnalysisAt' in t else None,'nextDueAt':iso(t['nextDueAt']) if 'nextDueAt' in t else None,'queued':bool(t.get('queueSince')),'error':t.get('error') or s.get('error') or ('stale_status' if s and not fresh else None)})
  return {'schema':'wapobook-analysis-dashboard-v1','generatedAt':iso(now),'enabled':not self.gates(),'blockedBy':self.gates(),'intervalSeconds':600,'maxConcurrent':self.config['maxConcurrent'],'targets':rows,'changes':copy.deepcopy(self.state['changes']),'dailyCostUsd':self.state['dailyCostUsd'],'realPilotPassed':self.config.get('realPilotPassed',False),'errors':copy.deepcopy(self.state.get('runErrors',[])[-20:])}
