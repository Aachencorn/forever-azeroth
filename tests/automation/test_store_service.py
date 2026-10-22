import unittest,tempfile,sys,asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'automation'))
from store import Store
from service import Service
from test_engine import fixture,status,obs,NOW
class Tests(unittest.TestCase):
 def test_two_workers_share_claims_and_restart_cooldown(self):
  s=fixture(3)
  with tempfile.TemporaryDirectory() as d:
   a=Store(Path(d)/'queue.sqlite3');a.initialize(s.archive);a.transaction(s.config,lambda x:x.state.update(s.state));b=Store(Path(d)/'queue.sqlite3')
   first=a.transaction(s.config,lambda x:x.reserve(NOW));second=b.transaction(s.config,lambda x:x.reserve(NOW));self.assertEqual(len(first),2);self.assertEqual(second,[])
   for j in first:b.transaction(s.config,lambda x:x.complete(j['id'],obs(j),NOW+30))
   restarted=Store(Path(d)/'queue.sqlite3');remaining=restarted.transaction(s.config,lambda x:x.reserve(NOW+31));self.assertEqual(len(remaining),1);self.assertNotIn(remaining[0]['personId'],[j['personId'] for j in first])
 def test_simultaneous_workers_do_not_double_claim(self):
  s=fixture(5)
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'queue.sqlite3';db=Store(path);db.initialize(s.archive);db.transaction(s.config,lambda x:x.state.update(s.state))
   def claim(_):return Store(path).transaction(s.config,lambda x:x.reserve(NOW))
   with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(claim,range(2)))
   self.assertEqual(sorted(map(len,results)),[0,2]);ids=[j['personId'] for group in results for j in group];self.assertEqual(len(ids),len(set(ids)))
 def test_transaction_rolls_back_and_no_reinitialize(self):
  s=fixture()
  with tempfile.TemporaryDirectory() as d:
   db=Store(Path(d)/'queue.sqlite3');db.initialize(s.archive);before=db.snapshot()
   def fail(system):system.archive['people'].clear();raise ValueError('test')
   self.assertRaises(ValueError,db.transaction,s.config,fail);self.assertEqual(db.snapshot(),before);self.assertRaises(Exception,db.initialize,s.archive)
 def test_missing_adapters_do_not_collect(self):
  s=fixture()
  with tempfile.TemporaryDirectory() as d:
   db=Store(Path(d)/'queue.sqlite3');db.initialize(s.archive);worker=Service(db,s.config)
   self.assertIn('blocked',asyncio.run(worker.status_tick()));self.assertIn('blocked',asyncio.run(worker.analysis_tick()));self.assertRaises(RuntimeError,asyncio.run,worker.run_forever())
if __name__=='__main__':unittest.main()
