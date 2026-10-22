"""Prepare a canonical archive from an administrator's existing backup; never reset it."""
import argparse,json,hashlib
from pathlib import Path
from public_data import project
p=argparse.ArgumentParser();p.add_argument('backup');p.add_argument('--output',default='automation/archive.json');a=p.parse_args();raw=Path(a.backup).read_bytes();data=json.loads(raw)
for key in ['people','guilds','slots']:
 if not isinstance(data.get(key),list):raise ValueError('Invalid backup: '+key)
for key in ['people','guilds']:
 ids=[r.get('id') for r in data[key]]
 if any(not isinstance(i,str) or not i for i in ids) or len(set(ids))!=len(ids):raise ValueError('Missing or duplicate IDs: '+key)
output=Path(a.output)
if output.exists():raise ValueError('Refusing to overwrite an existing canonical archive')
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(project(data),ensure_ascii=False,indent=2)+'\n')
print('Prepared public records; administrator reports/unknown private fields omitted; original backup unchanged; sha256='+hashlib.sha256(raw).hexdigest()+'. Review the file before publication. No site data was changed.')
