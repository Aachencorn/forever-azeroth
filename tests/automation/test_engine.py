import unittest,json,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'automation'))
from engine import System,new_state,iso
from public_data import project,public_dashboard
NOW=1792713600

def fixture(n=1):
 c=json.loads((ROOT/'automation/config.json').read_text());c.update({k:True for k in ['enabled','statusAccessVerified','videoAnalysisPermitted','realPilotPassed','migrationApproved']});c.update(estimatedCostPerAnalysisUsd=.01,dailyBudgetUsd=10)
 a={'people':[],'guilds':[{'id':'old','name':'원래길드'},{'id':'new','name':'새길드'}],'slots':['p0']+['']*19,'reports':[{'private':'do-not-publish'}],'settings':{'siteName':'와포북','secret':'do-not-publish'}}
 for i in range(n):
  aid='test'+str(i);c['approvedAccounts'][aid]={'analysisAllowed':True};a['people'].append({'id':'p'+str(i),'name':'검증'+str(i),'soop':aid,'image':'keep-photo','characters':[{'id':'c'+str(i),'name':'본인'+str(i),'main':True,'level':'20','guildId':'old'}]})
 s=System(a,new_state(),c)
 for p in a['people']:s.set_enabled(p['id'],True,'tester',NOW)
 status(s,NOW);return s

def status(s,t,kind='streaming'):
 s.ingest_statuses([{'accountId':'test'+str(i),'status':kind,'broadcastId':'b'+str(i),'game':'wow','realm':'forever','classificationVerified':True,'checkedAt':iso(t)} for i,_ in enumerate(s.archive['people'])],t)
def obs(job,level=21,guild='원래길드',score=.995,name=None):
 i=int(job['personId'][1:]);return {'sourceType':'authorized-live-sample','accountId':job['accountId'],'broadcastId':job['broadcastId'],'actualCostUsd':.008,'frames':[{'frameId':job['id']+'-'+str(x),'capturedAt':iso(job['startedAt']+10+x*10),'characterName':name or '본인'+str(i),'level':level,'guildName':guild,'scene':'self-character-sheet','selfConfirmed':True,'confidence':score} for x in range(2)]}
class Tests(unittest.TestCase):
 def test_disabled_and_missing_real_pilot_never_reserve(self):
  s=fixture();s.config['enabled']=False;self.assertEqual(s.reserve(NOW),[]);s.config['enabled']=True;s.config['realPilotPassed']=False;self.assertEqual(s.reserve(NOW),[])
 def test_180_queue_concurrency_and_ten_minute_cooldown(self):
  s=fixture(180);jobs=s.reserve(NOW);self.assertEqual(len(jobs),2);self.assertEqual(s.reserve(NOW+1),[])
  for j in jobs:s.complete(j['id'],obs(j),NOW+30)
  other=s.reserve(NOW+31);self.assertEqual(len(other),2);self.assertTrue(set(j['personId'] for j in jobs).isdisjoint(j['personId'] for j in other))
  single=fixture();j=single.reserve(NOW)[0];single.complete(j['id'],obs(j),NOW+30);status(single,NOW+599);self.assertEqual(single.reserve(NOW+599),[]);status(single,NOW+600);self.assertEqual(len(single.reserve(NOW+600)),1)
 def test_only_wow_forever_with_per_streamer_permission(self):
  for key,value in [('game','other'),('realm','other'),('classificationVerified',False),('status','streamend')]:
   s=fixture();s.state['statuses']['p0'][key]=value;self.assertEqual(s.reserve(NOW),[])
  s=fixture();s.config['approvedAccounts']={};self.assertEqual(s.reserve(NOW),[])
 def test_stale_status_no_work(self):
  s=fixture();self.assertEqual(s.reserve(NOW+121),[])
 def test_verified_level_increase_and_idempotence(self):
  s=fixture();j=s.reserve(NOW)[0];o=obs(j);self.assertEqual(s.complete(j['id'],o,NOW+30),'processed');self.assertEqual(s.archive['people'][0]['characters'][0]['level'],'21');self.assertEqual(s.complete(j['id'],o,NOW+31),'duplicate_or_closed_job');self.assertEqual(len(s.state['changes']),1);self.assertEqual(sum(s.state['dailyCostUsd'].values()),.008)
 def test_low_confidence_identity_and_decrease_stay_pending(self):
  for args in [{'score':.8},{'name':'타인'},{'level':19},{'level':25}]:
   s=fixture();j=s.reserve(NOW)[0];s.complete(j['id'],obs(j,**args),NOW+30);self.assertEqual(s.archive['people'][0]['characters'][0]['level'],'20');self.assertEqual(s.state['changes'][0]['status'],'pending')
 def test_guild_needs_approval_and_preserves_history(self):
  s=fixture();j=s.reserve(NOW)[0];s.complete(j['id'],obs(j,level=20,guild='새길드'),NOW+30);c=s.state['changes'][0];char=s.archive['people'][0]['characters'][0];self.assertEqual(char['guildId'],'old');s.decide(c['id'],'approve','reviewer',NOW+40);self.assertEqual(char['guildId'],'new');self.assertEqual(char['guildHistory'][0]['guildId'],'old');s.decide(c['id'],'restore','reviewer',NOW+50);self.assertEqual(char['guildId'],'old');self.assertEqual(len(char['guildHistory']),2)
 def test_unknown_guild_cannot_be_approved_as_id(self):
  s=fixture();j=s.reserve(NOW)[0];s.complete(j['id'],obs(j,20,'없는길드'),NOW+30);c=s.state['changes'][0];self.assertEqual(c['field'],'unmapped_guild');self.assertRaises(ValueError,s.decide,c['id'],'approve','reviewer',NOW+40)
 def test_reject_and_repeated_change_deduplicate(self):
  s=fixture();j=s.reserve(NOW)[0];s.complete(j['id'],obs(j,19),NOW+30);c=s.state['changes'][0];s.decide(c['id'],'reject','reviewer',NOW+40);status(s,NOW+600);j=s.reserve(NOW+600)[0];s.complete(j['id'],obs(j,19),NOW+630);self.assertEqual(len(s.state['changes']),1);self.assertEqual(c['status'],'rejected')
 def test_restore_does_not_overwrite_later_change(self):
  s=fixture();j=s.reserve(NOW)[0];s.complete(j['id'],obs(j),NOW+30);c=s.state['changes'][0];s.archive['people'][0]['characters'][0]['level']='22';self.assertRaises(ValueError,s.decide,c['id'],'restore','reviewer',NOW+40)
 def test_broadcast_end_disablement_and_manual_edit_preserve(self):
  for mode in ['offline','disabled','edit','new_broadcast']:
   s=fixture();j=s.reserve(NOW)[0]
   if mode=='offline':status(s,NOW+10,'streamend')
   if mode=='disabled':s.set_enabled('p0',False,'reviewer',NOW+10)
   if mode=='edit':s.archive['people'][0]['characters'][0]['level']='30'
   if mode=='new_broadcast':s.state['statuses']['p0']['broadcastId']='replacement'
   before=copy.deepcopy(s.archive);s.complete(j['id'],obs(j),NOW+30);self.assertEqual(s.archive,before)
 def test_insufficient_duplicate_and_inconsistent_frames(self):
  for mode in ['one','duplicate','future','other_account','conflicting']:
   s=fixture();j=s.reserve(NOW)[0];o=obs(j)
   if mode=='one':o['frames']=o['frames'][:1]
   if mode=='duplicate':o['frames'][1]['frameId']=o['frames'][0]['frameId']
   if mode=='future':o['frames'][1]['capturedAt']=iso(NOW+1000)
   if mode=='other_account':o['accountId']='someone_else'
   if mode=='conflicting':o['frames'][1]['level']=22
   s.complete(j['id'],o,NOW+30);self.assertEqual(s.archive['people'][0]['characters'][0]['level'],'20')
 def test_failure_expired_lease_and_cost_budget(self):
  s=fixture();s.config['dailyBudgetUsd']=.01;j=s.reserve(NOW)[0];o=obs(j);o.pop('actualCostUsd');s.complete(j['id'],o,NOW+30);status(s,NOW+600);self.assertEqual(s.reserve(NOW+600),[]);self.assertTrue(s.state['jobs'][j['id']]['costEstimated'])
  s=fixture();j=s.reserve(NOW)[0];s.complete(j['id'],obs(j),NOW+301);self.assertEqual(s.archive['people'][0]['characters'][0]['level'],'20');self.assertEqual(sum(s.state['dailyCostUsd'].values()),.01)
 def test_public_projection_no_private_reports(self):
  s=fixture();result=project(s.archive);self.assertNotIn('reports',result);self.assertNotIn('secret',result['settings']);self.assertEqual(s.archive['reports'][0]['private'],'do-not-publish')
 def test_status_duplicates_are_unknown(self):
  s=fixture();row=dict(s.state['statuses']['p0']);s.ingest_statuses([row,row],NOW);self.assertEqual(s.state['statuses']['p0']['status'],'unknown');self.assertEqual(s.reserve(NOW),[])
 def test_duplicate_registered_accounts_are_not_analyzed(self):
  s=fixture(2);s.archive['people'][1]['soop']=s.archive['people'][0]['soop'];self.assertEqual(s.reserve(NOW),[])
 def test_non_finite_confidence_is_not_applied(self):
  s=fixture();j=s.reserve(NOW)[0];o=obs(j);o['frames'][1]['confidence']=float('nan');s.complete(j['id'],o,NOW+30);self.assertEqual(s.archive['people'][0]['characters'][0]['level'],'20')
 def test_vod_calibration_cannot_update_live_records(self):
  s=fixture();j=s.reserve(NOW)[0];o=obs(j);o['sourceType']='authorized-vod-calibration';s.complete(j['id'],o,NOW+30);self.assertEqual(s.archive['people'][0]['characters'][0]['level'],'20');self.assertEqual(s.state['changes'],[])
 def test_interval_is_fixed(self):
  s=fixture();s.config['analysisIntervalSeconds']=60;self.assertRaises(ValueError,System,s.archive,s.state,s.config)
if __name__=='__main__':unittest.main()
