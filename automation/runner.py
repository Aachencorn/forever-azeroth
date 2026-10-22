"""Replay normalized, authorized provider reports. Does NOT collect or analyze video.
Writes review artifacts only unless explicit publication and migration gates pass.
"""
import argparse,json,os,time
from pathlib import Path
from engine import System,new_state
from public_data import project,public_dashboard
ROOT=Path(__file__).resolve().parents[1]
def read(path,default=None):return json.loads(Path(path).read_text()) if path and Path(path).exists() else default
def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
def main():
 p=argparse.ArgumentParser();p.add_argument('--archive',default='automation/archive.json');p.add_argument('--state',default='automation/state.json');p.add_argument('--config',default='automation/config.json');p.add_argument('--statuses');p.add_argument('--observations');p.add_argument('--decisions');p.add_argument('--out',default='artifacts/analysis');p.add_argument('--publish',action='store_true');a=p.parse_args()
 config=read(a.config);archive=read(a.archive);now=time.time();out=Path(a.out)
 if not archive:
  write(out/'dashboard.json',{'schema':'wapobook-analysis-dashboard-v1','generatedAt':None,'enabled':False,'blockedBy':['archive_not_migrated','status_provider_not_implemented','video_provider_not_implemented','real_pilot_not_run'],'intervalSeconds':600,'maxConcurrent':config['maxConcurrent'],'targets':[],'changes':[],'dailyCostUsd':{},'realPilotPassed':False});print('Blocked: canonical archive is not migrated; no collection or publication performed.');return
 if not isinstance(archive.get('people'),list) or not isinstance(archive.get('guilds'),list):raise ValueError('invalid_archive')
 system=System(archive,read(a.state,new_state()),config)
 for d in read(a.decisions,[]):
  actor=os.environ.get('GITHUB_ACTOR') or 'local-reviewer'
  if d.get('type')=='target-enabled':system.set_enabled(d['personId'],d['enabled'],actor,now)
  else:system.decide(d['changeId'],d['decision'],actor,now)
 if a.statuses:system.ingest_statuses(read(a.statuses,[]),now)
 # Accept existing leased-job observations first, then reserve more work.
 for obs in read(a.observations,[]):system.complete(obs['jobId'],obs,now)
 jobs=system.reserve(now)
 for name,value in [('archive.json',system.archive),('state.json',system.state),('dashboard.json',system.dashboard(now)),('reserved-jobs.json',jobs)]:write(out/name,value)
 if a.publish:
  if system.gates() or not config.get('publicationEnabled'):raise ValueError('publication_not_approved')
  # One client-visible object contains an atomic data+audit revision.
  publication={'schema':'wapobook-public-archive-v1','revision':system.dashboard(now)['generatedAt'],'archive':project(system.archive),'dashboard':public_dashboard(system.dashboard(now))}
  write('data/published-archive.json',publication)
 print(json.dumps({'blockedBy':system.gates(),'reserved':len(jobs),'pending':sum(c['status']=='pending' for c in system.state['changes']),'published':a.publish}))
if __name__=='__main__':main()
