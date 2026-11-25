import copy, json, plistlib, sys, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import core
import jsonschema
from ipa import inspect_ipa
APP={'name':'Test','bundleIdentifier':'org.example.test','developerName':'Dev','localizedDescription':'Test app','iconURL':'https://example.org/icon.png','versions':[{'version':'1.0','buildVersion':'2','date':'2026-11-25','downloadURL':'https://example.org/test.ipa','size':123}]}
class SourceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.patch=patch.object(core,'ROOT',Path(self.tmp.name));self.patch.start()
  self.c={'sources':[{'id':'a','url':'https://example.org/source','selected':{'org.example.test':True}}],'manualApps':[]};core.write('config.json',self.c)
 def tearDown(self):self.patch.stop();self.tmp.cleanup()
 def remote(self,url):return {'apps':[copy.deepcopy(APP)]}
 def test_failure_preserves_last_good(self):
  first=core.update(self.remote)
  def fail(url):raise ValueError('403')
  self.assertEqual(first,core.update(fail));self.assertFalse(core.load('status.json')['messages'][0]['ok'])
 def test_invalid_update_preserves_good(self):
  core.update(self.remote);bad=copy.deepcopy(APP);bad['versions'][0]['size']=0
  self.assertEqual(core.update(lambda u:{'apps':[bad]})['apps'][0]['versions'][0]['size'],123)
 def test_freeze_and_deselect(self):
  core.update(self.remote);self.c['sources'][0]['selected']['org.example.test']=False;core.write('config.json',self.c)
  new=copy.deepcopy(APP);new['versions'][0]['version']='2';self.assertEqual(core.update(lambda u:{'apps':[new]})['apps'][0]['versions'][0]['version'],'1.0')
  self.c['sources'][0]['selected']={};core.write('config.json',self.c);self.assertEqual(core.update(self.remote)['apps'],[])
 def test_manual_wins_duplicate(self):
  manual=copy.deepcopy(APP);manual['name']='Manual';self.c['manualApps']=[manual];core.write('config.json',self.c)
  self.assertEqual(core.update(self.remote)['apps'][0]['name'],'Manual')
 def test_legacy_and_version_order(self):
  a=copy.deepcopy(APP);v=a.pop('versions')[0];a.update(version=v['version'],versionDate=v['date'],size=v['size'],downloadURL=v['downloadURL'])
  self.assertEqual(core.normalize(a)['versions'][0]['version'],'1.0')
  a=copy.deepcopy(APP);a['versions'].append(dict(a['versions'][0],version='0.9'));self.assertEqual(core.normalize(a)['versions'][0]['buildVersion'],'2')
 def test_invalid_urls(self):
  for u in ['http://example.com','https://user:pass@example.com','file:///etc/passwd']:
   with self.assertRaises(ValueError):core.url(u)
  with self.assertRaises(ValueError):core.public_url('https://127.0.0.1/x')
 def test_ipa_metadata(self):
  p=Path(self.tmp.name)/'x.ipa'
  with zipfile.ZipFile(p,'w') as z:z.writestr('Payload/Test.app/Info.plist',plistlib.dumps({'CFBundleIdentifier':'org.test','CFBundleShortVersionString':'3','CFBundleVersion':'7','CFBundleName':'Sample','MinimumOSVersion':'15.0'}))
  a,icon=inspect_ipa(p);self.assertEqual(a['versions'][0]['buildVersion'],'7');self.assertEqual(a['versions'][0]['size'],p.stat().st_size);self.assertIsNone(icon)
 def test_strict_sidestore_projection(self):
  core.update(self.remote);side=core.load('sidestore.json');self.assertNotIn('buildVersion',side['apps'][0]['versions'][0])
  schema=json.loads((Path(__file__).resolve().parents[1]/'vendor/sidestore.schema.json').read_text())
  def check(obj,kind):
   d=schema['definitions'][kind];self.assertTrue(set(d['required'])<=obj.keys());self.assertTrue(obj.keys()<=d['properties'].keys())
  jsonschema.validate(side,schema)
  check(side,'Source');check(side['apps'][0],'App');check(side['apps'][0]['versions'][0],'Version')
if __name__=='__main__':unittest.main()
