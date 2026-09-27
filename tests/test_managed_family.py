import unittest,json
from unittest.mock import Mock
from core.managed_family import ManagedFamily
from core.telegram_api import DEFAULT_ALLOWED_UPDATES
from core.telegram_events import TelegramEventStore
from tests.test_personal_rss_runtime import DB

class FamilyTests(unittest.TestCase):
 def setUp(self):
  self.db=DB();self.bot=Mock(token='1:parent',bot_username='CintiaBot')
  self.db.set('CHATS_1:parent',['-10','123'])
  self.rights=True
  def api(method,args):
   if method=='getChat':return {'ok':True,'result':{'id':22}}
   if method=='getManagedBotToken':return {'ok':True,'result':'22:private'}
   if method=='getChatMember':return {'ok':True,'result':{'status':'administrator','can_delete_messages':self.rights,'can_restrict_members':self.rights}}
   self.fail('Unexpected Telegram method '+method)
  self.bot.api_call.side_effect=api
  self.s=ManagedFamily(self.db,lambda:[self.bot],lambda value:'encrypted')
 def test_enroll_encrypted_without_starting_or_sending(self):
  self.s.sync();snapshot=self.s.snapshot();row=snapshot['children'][0]
  self.assertEqual(row['status'],'permissions_verified');self.assertEqual(row['verified_groups'],1)
  self.assertFalse(row['automatic_failover']);self.assertNotIn('private',json.dumps(snapshot));self.assertNotIn('token',json.dumps(snapshot))
  self.assertEqual(self.db.get('MANAGED_CHILD_SECRET_22')['token'],'encrypted')
  self.bot.run.assert_not_called();self.bot.send_msg.assert_not_called()
 def test_lost_permissions_and_wrong_parent(self):
  self.s.sync();self.rights=False;self.s.sync();self.assertEqual(self.s.snapshot()['children'][0]['verified_groups'],0)
  self.bot.api_call.side_effect=lambda method,args: {'ok':True,'result':{'id':22}} if method=='getChat' else {'ok':False}
  self.s.sync();self.assertEqual(self.s.snapshot()['children'][0]['status'],'relationship_unverified')
 def test_api_failure_not_ready(self):
  self.bot.api_call.side_effect=RuntimeError('private');self.s.sync()
  self.assertEqual(self.s.snapshot()['children'][0]['status'],'verification_unavailable')
  self.assertNotIn('private',json.dumps(self.s.snapshot()))
 def test_managed_updates_and_service_message(self):
  self.assertIn('managed_bot',DEFAULT_ALLOWED_UPDATES)
  store=TelegramEventStore(self.db,Mock())
  self.assertTrue(store.record_managed_bot_update({'message':{'managed_bot_created':{'bot':{'id':22}}}}))
  self.assertEqual(len(self.db.get('MANAGED_BOT_UPDATES')),1)
