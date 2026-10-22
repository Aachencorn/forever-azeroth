"""Sanitize artifacts when used in the public website repository."""
import json
from pathlib import Path
from public_data import public_dashboard
source=Path('artifacts/analysis/dashboard.json')
if source.exists():
 out=Path('artifacts/public-review');out.mkdir(parents=True,exist_ok=True);(out/'dashboard.json').write_text(json.dumps(public_dashboard(json.loads(source.read_text())),ensure_ascii=False,indent=2)+'\n')
