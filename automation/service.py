"""Two independent worker loops. Production provider adapters are NOT supplied.
Authorized provider interfaces:
 status_provider.fetch_statuses(people) -> normalized status rows
 analysis_provider.analyze(job, maximum_frames=3) -> normalized evidence+metered cost
No browser, stream extraction or capture fallback exists in this module.
"""
import asyncio,time
from engine import iso
class Service:
 def __init__(self,store,config,status_provider=None,analysis_provider=None,clock=time.time):
  self.store=store;self.config=config;self.status_provider=status_provider;self.analysis_provider=analysis_provider;self.clock=clock
 async def status_tick(self):
  if self.config.get('enabled') is not True or self.config.get('statusAccessVerified') is not True or self.status_provider is None:return {'blocked':'status_provider_not_verified_or_missing'}
  snapshot,_=self.store.snapshot()
  try:rows=await self.status_provider.fetch_statuses(snapshot['archive']['people'])
  except Exception:
   self.store.transaction(self.config,lambda s:s.state['runErrors'].append({'phase':'status','error':'provider_failed','at':iso(self.clock())}));return {'error':'status_provider_failed'}
  try:self.store.transaction(self.config,lambda s:s.ingest_statuses(rows,self.clock()))
  except Exception:return {'error':'invalid_status_report'}
  return {'received':len(rows)}
 async def analysis_tick(self):
  if self.analysis_provider is None:return {'blocked':'analysis_provider_missing'}
  jobs=self.store.transaction(self.config,lambda s:s.reserve(self.clock()))
  async def execute(job):
   try:
    async with asyncio.timeout(self.config['leaseSeconds']-5):report=await self.analysis_provider.analyze(job,maximum_frames=self.config['maximumEvidenceFrames'])
   except Exception:report={'error':'analysis_provider_failed'}
   if not isinstance(report,dict):report={'error':'invalid_analysis_report'}
   return self.store.transaction(self.config,lambda s:s.complete(job['id'],report,self.clock()))
  return await asyncio.gather(*(execute(j) for j in jobs))
 async def run_forever(self):
  if self.status_provider is None or self.analysis_provider is None:raise RuntimeError('Production status/video/OCR adapters are not implemented. Do not start collection.')
  async def statuses():
   while True:await self.status_tick();await asyncio.sleep(60)
  async def analyses():
   while True:await self.analysis_tick();await asyncio.sleep(1)
  await asyncio.gather(statuses(),analyses())

if __name__=='__main__':raise SystemExit('Blocked: production status and video/OCR provider adapters are not connected. No collection started.')
