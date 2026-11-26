import sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import publish
class PublishTests(unittest.TestCase):
 def test_staged_changes_blocked(self):
  with patch.object(publish,'command',side_effect=['main','https://github.com/parkace-ipa/my-ios-source.git','web/app.js']):
   with self.assertRaisesRegex(ValueError,'다른 변경'):publish.preflight()
 def test_conflict_aborts_without_push(self):
  calls=[]
  def cmd(*args):
   calls.append(args)
   if args[:3]==('git','diff','--cached'):return 'config.json'
   if args==('git','rebase','origin/main'):raise ValueError('conflict')
   return ''
  with patch.object(publish,'command',side_effect=cmd):
   with self.assertRaisesRegex(ValueError,'충돌'):publish.publish()
  self.assertIn(('git','rebase','--abort'),calls)
  self.assertFalse(any(c[:2]==('git','push') for c in calls))
 def test_unchanged_dispatches_workflow(self):
  calls=[]
  def cmd(*args):
   calls.append(args)
   return 'a'*40 if args[:2]==('git','rev-parse') else ''
  with patch.object(publish,'command',side_effect=cmd):publish.publish()
  self.assertTrue(any(c[:3]==('gh','workflow','run') for c in calls))
 def test_old_run_not_reported_as_success(self):
  with patch.object(publish,'command',return_value='[{"createdAt":"2026-11-25T00:00:00Z","status":"completed","conclusion":"success"}]'):
   self.assertEqual(publish.status('a'*40,'2026-11-26T00:00:00Z')['status'],'queued')
