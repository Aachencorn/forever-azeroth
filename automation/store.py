"""Durable single-host queue state with SQLite transactions (not browser storage)."""
import json,sqlite3
from pathlib import Path
from contextlib import closing
from engine import System,new_state
class Store:
 def __init__(self,path):
  self.path=str(path);Path(path).parent.mkdir(parents=True,exist_ok=True)
  with closing(self.connect()) as db:db.execute('CREATE TABLE IF NOT EXISTS archive_state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, revision INTEGER NOT NULL)')
 def connect(self):
  db=sqlite3.connect(self.path,timeout=30,isolation_level=None);db.execute('PRAGMA busy_timeout=30000');return db
 def initialize(self,archive):
  with closing(self.connect()) as db:
   db.execute('BEGIN IMMEDIATE')
   try:db.execute('INSERT INTO archive_state VALUES (1,?,1)',(json.dumps({'archive':archive,'state':new_state()},ensure_ascii=False),));db.commit()
   except Exception:db.rollback();raise
 def transaction(self,config,operation):
  with closing(self.connect()) as db:
   db.execute('BEGIN IMMEDIATE')
   try:
    row=db.execute('SELECT payload,revision FROM archive_state WHERE id=1').fetchone()
    if not row:raise ValueError('canonical_archive_not_initialized')
    payload=json.loads(row[0]);system=System(payload['archive'],payload['state'],config);result=operation(system)
    db.execute('UPDATE archive_state SET payload=?,revision=? WHERE id=1',(json.dumps({'archive':system.archive,'state':system.state},ensure_ascii=False),row[1]+1));db.commit();return result
   except Exception:db.rollback();raise
 def snapshot(self):
  with closing(self.connect()) as db:
   row=db.execute('SELECT payload,revision FROM archive_state WHERE id=1').fetchone()
   if not row:raise ValueError('canonical_archive_not_initialized')
   return json.loads(row[0]),row[1]
