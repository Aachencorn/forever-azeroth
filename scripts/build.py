"""Validate and bundle this dependency-free static site; output defaults to dist/."""
from pathlib import Path
import re, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
for source in ['app.js','final-book.js','exact-design.js','tavern-home.js','admin-import-core.js','admin-import.js']:
 subprocess.run(['node','--check',str(ROOT/source)],check=True)
for path in ['index.html','app.js','final-book.js','styles.css','styles/final-book-theme.css','data/official-news.json','assets/wapobook/final-atlas.webp']:
 assert (ROOT/path).is_file(),path
html=(ROOT/'index.html').read_text()
for ref in re.findall(r'(?:src|href)="([^"?#]+)',html):
 if not re.match(r'https?://',ref):assert (ROOT/ref).is_file(),ref
for name in ['styles/final-book-theme.css','styles/review-fixes.css','styles/exact-design.css','styles/tavern-redesign.css']:
 css=ROOT/name
 for ref in re.findall(r'url\([\'"]?([^\)\'\"]+)',css.read_text()):
  if not ref.startswith(('data:','https:','#')):assert (css.parent/ref).is_file(),ref
if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir()
for name in ['index.html','app.js','final-book.js','exact-design.js','tavern-home.js','admin-import-core.js','admin-import.js','styles.css','forever-city.webp']:
 shutil.copy2(ROOT/name,OUT/name)
for name in ['assets','styles','data','downloads','vendor']:
 shutil.copytree(ROOT/name,OUT/name)
print(f'Build OK: {sum(1 for p in OUT.rglob("*") if p.is_file())} files -> {OUT}')
