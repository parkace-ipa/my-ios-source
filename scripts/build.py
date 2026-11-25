import shutil
from core import ROOT
out=ROOT/'dist'
if out.exists(): shutil.rmtree(out)
out.mkdir()
for p in (ROOT/'web').iterdir():
    if p.is_file(): shutil.copy(p,out/p.name)
for name in ('source.json','sidestore.json'):
    shutil.copy(ROOT/name,out/name)
(out/'.nojekyll').touch()
print('Built dist/')
