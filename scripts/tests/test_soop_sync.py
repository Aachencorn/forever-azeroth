import importlib.util,io,json,unittest
from urllib.error import HTTPError
from pathlib import Path
from datetime import datetime,timezone
spec=importlib.util.spec_from_file_location('soop',Path(__file__).parents[1]/'sync_soop_profiles.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
CONFIG={'enabled':True,'policyReviewed':True,'profileLinkingPermitted':True,'reviewReference':'test fixture only','documentationUrl':'https://openapi.sooplive.com/','sourceType':'station-profile','endpointTemplate':'https://openapi.sooplive.com/test/{accountId}','accountIdPath':'user.id','profileImagePath':'user.profile','secretHeaders':{},'cacheHours':24,'requestIntervalSeconds':2}
class Response(io.BytesIO):
 def __init__(self,b,ctype='application/json'):super().__init__(b);self.headers={'Content-Type':ctype}
class Tests(unittest.TestCase):
 def test_disabled_never_requests(self):
  class Never:
   def resolve(self,aid):raise AssertionError('must not request')
  req={'schema':'wapobook-soop-requests-v1','accounts':[{'accountId':'test'+str(i)} for i in range(5)]}
  r=s.run(req,{},resolver=Never());self.assertEqual({x['status'] for x in r['results']},{'blocked'})
 def test_bulk_requires_pilot(self):
  req={'schema':'wapobook-soop-requests-v1','accounts':[{'accountId':'test'+str(i)} for i in range(180)]}
  self.assertEqual(len(s.run(req,CONFIG,'batch')['results']),180)
  self.assertEqual(s.run(req,CONFIG,'batch')['results'][0]['status'],'blocked')
 def test_success_cache_and_head(self):
  calls=[];waits=[];cache={}
  def request(req,timeout):
   calls.append((req.full_url,req.method))
   return Response(b'', 'image/jpeg') if req.method=='HEAD' else Response(json.dumps({'user':{'id':'test0','profile':'https://profile.img.sooplive.com/LOGO/te/test0/test0.jpg'}}).encode())
  r=s.Resolver(CONFIG,cache,request,waits.append,lambda:100)
  self.assertEqual(r.resolve('test0')['status'],'success');self.assertTrue(r.resolve('test0')['cached']);self.assertEqual(len(calls),2);self.assertIn(2,waits)
 def test_wrong_identity_and_thumbnail(self):
  for payload in [{'user':{'id':'wrong','profile':'x'}},{'user':{'id':'test0','profile':'https://liveimg.sooplive.com/thumbnail.jpg'}}]:
   r=s.Resolver(CONFIG,{},lambda req,timeout:Response(json.dumps(payload).encode()),lambda n:None)
   self.assertEqual(r.resolve('test0')['status'],'failed')
 def test_auth_circuit_and_transient_retry(self):
  calls=[]
  def denied(req,timeout):calls.append(1);raise HTTPError(req.full_url,403,'Forbidden',{},None)
  r=s.Resolver(CONFIG,{},denied,lambda n:None);r.resolve('test0');r.resolve('test1');self.assertEqual(len(calls),1)
  def transient(req,timeout):calls.append(1);raise HTTPError(req.full_url,429,'Rate limited',{'Retry-After':'3'},None)
  waits=[];calls.clear();r=s.Resolver(CONFIG,{},transient,waits.append,lambda:100);r.resolve('test0');self.assertEqual(len(calls),3);self.assertIn(3,waits)
 def test_pilot_proof(self):
  proof={'schema':'wapobook-soop-profiles-v1','mode':'pilot','configFingerprint':s.fingerprint(CONFIG),'generatedAt':datetime.now(timezone.utc).isoformat(),'results':[{'accountId':'test'+str(i),'status':'success','imageUrl':f'https://profile.img.sooplive.com/LOGO/te/test{i}/test{i}.jpg'} for i in range(5)]}
  self.assertTrue(s.pilot_valid(proof,CONFIG));proof['results'].pop();self.assertFalse(s.pilot_valid(proof,CONFIG))
if __name__=='__main__':unittest.main()
