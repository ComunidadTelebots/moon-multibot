import unittest
from unittest.mock import Mock
from core.managed_group_onboarding import prepare_group,GROUP_ID,CHILD_ID
from tests.test_personal_rss_runtime import DB
class OnboardingTests(unittest.TestCase):
 def setUp(self):
  self.db=DB();self.parent=Mock(token='1:secret',bot_username='CintiaBot');self.status='left';self.allow=True;self.managed=True
  def api(method,args):
   self.assertEqual(str(args.get('chat_id',GROUP_ID)),GROUP_ID)
   if method=='getChatMember':
    if str(args['user_id'])=='1':return {'ok':True,'result':{'status':'administrator','can_promote_members':self.allow,'can_delete_messages':True,'can_restrict_members':True}}
    return {'ok':True,'result':{'status':self.status,'can_delete_messages':self.status=='administrator','can_restrict_members':self.status=='administrator'}}
   if method=='getManagedBotToken':return {'ok':self.managed,'result':str(CHILD_ID)+':secret'}
   if method=='sendMessage':return {'ok':True,'result':{'message_id':10}}
   if method=='promoteChatMember':self.status='administrator';return {'ok':True}
   self.fail(method)
  self.parent.api_call.side_effect=api
 def calls(self,method):return [c for c in self.parent.api_call.call_args_list if c.args[0]==method]
 def test_absent_child_only_prompts_on_explicit_request_once(self):
  self.assertEqual(prepare_group(self.parent,self.db),'awaiting_addition');self.assertFalse(self.calls('sendMessage'))
  prepare_group(self.parent,self.db,send_prompt=True);prepare_group(self.parent,self.db,send_prompt=True)
  self.assertEqual(len(self.calls('sendMessage')),1);self.assertFalse(self.calls('promoteChatMember'))
 def test_promotes_present_managed_child_with_minimum_rights(self):
  self.status='member';self.assertEqual(prepare_group(self.parent,self.db),'permissions_ready')
  params=self.calls('promoteChatMember')[0].args[1]
  self.assertTrue(params['can_delete_messages']);self.assertFalse(params['can_promote_members']);self.assertFalse(params['can_invite_users'])
  prepare_group(self.parent,self.db);self.assertEqual(len(self.calls('promoteChatMember')),1)
 def test_missing_parent_rights_and_unverified_relationship_fail_closed(self):
  self.status='member';self.allow=False;self.assertEqual(prepare_group(self.parent,self.db),'parent_permissions_missing')
  self.allow=True;self.managed=False;self.assertEqual(prepare_group(self.parent,self.db),'relationship_unverified');self.assertFalse(self.calls('promoteChatMember'))
 def test_uncertain_prompt_not_repeated(self):
  original=self.parent.api_call.side_effect
  self.parent.api_call.side_effect=lambda method,args: {'ok':False} if method=='sendMessage' else original(method,args)
  prepare_group(self.parent,self.db,send_prompt=True);prepare_group(self.parent,self.db,send_prompt=True)
  self.assertEqual(len(self.calls('sendMessage')),1)
 def test_other_parent_does_nothing(self):
  self.parent.bot_username='AnotherBot';self.assertEqual(prepare_group(self.parent,self.db,send_prompt=True),'wrong_parent');self.parent.api_call.assert_not_called()
