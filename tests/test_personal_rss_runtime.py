import copy
import datetime
import unittest
from unittest.mock import Mock, patch
from core.personal_rss_runtime import PersonalRssService

class DB:
    def __init__(self): self.data={'CHATS_secret':['123'],'GROUP_RSS_GROUPS':['123']}
    def get(self,k,d=None):return copy.deepcopy(self.data.get(k,d))
    def set(self,k,v):self.data[k]=copy.deepcopy(v)

class PersonalRssTests(unittest.TestCase):
    def setUp(self):
        self.db=DB(); self.bot=Mock(token='secret');self.bot.api_call.return_value={'ok':True,'result':{'status':'left'}}
        self.bot.send_msg.return_value={'ok':True}
        self.now=datetime.datetime(2026,9,27,tzinfo=datetime.timezone.utc)
        self.s=PersonalRssService(self.db,lambda:[self.bot],clock=lambda:self.now)
        self.s.admin_checks['secret']=(__import__('time').monotonic(),True)
        self.sleep_patch=patch('core.personal_rss_runtime.time.sleep');self.sleep_patch.start();self.addCleanup(self.sleep_patch.stop)
        self.s.manager=Mock();self.s.manager.list.return_value=[{'id':'one','enabled':True}]
        self.s.manager.poll.return_value=[{'id':str(i),'feed_id':'one','title':'news','url':'https://example.com'} for i in range(3)]
    def test_exact_daily_boundary_and_global_feed_quota(self):
        self.db.set('PERSONAL_RSS_DAILY_123',{'day':'2026-09-27','used':49})
        self.s.cycle();self.bot.send_msg.assert_called_once();self.assertEqual(self.s.quota('123')['used'],50)
        self.s.cycle();self.bot.send_msg.assert_called_once()
    def test_member_can_continue(self):
        self.db.set('PERSONAL_RSS_DAILY_123',{'day':'2026-09-27','used':50})
        self.bot.api_call.return_value={'ok':True,'result':{'status':'member'}}
        self.s.cycle();self.assertEqual(self.bot.send_msg.call_count,3)
    def test_error_is_not_membership(self):
        self.bot.api_call.return_value={'ok':False}
        self.db.set('PERSONAL_RSS_DAILY_123',{'day':'2026-09-27','used':50})
        self.s.cycle();self.bot.send_msg.assert_not_called()
        self.assertEqual(self.s.allowance('123')['membership'],'unavailable')
    def test_reset_at_utc_midnight(self):
        self.db.set('PERSONAL_RSS_DAILY_123',{'day':'2026-09-26','used':99})
        self.assertEqual(self.s.quota('123')['used'],0)
    def test_ambiguous_delivery_is_not_replayed(self):
        self.bot.send_msg.return_value=None
        self.s.cycle();self.s.cycle();self.bot.send_msg.assert_called_once()
        self.assertTrue(self.s.allowance('123')['delivery_uncertain'])
    def test_unknown_private_chat_does_not_send(self):
        self.db.set('CHATS_secret',[]);self.s.cycle();self.bot.send_msg.assert_not_called()
    def test_group_targets_not_handled_by_private_scheduler(self):
        self.db.set('GROUP_RSS_GROUPS',['-99']);self.s.cycle();self.bot.send_msg.assert_not_called()
    def test_membership_cache_and_leave(self):
        self.bot.api_call.return_value={'ok':True,'result':{'status':'member'}}
        self.assertEqual(self.s.membership('123'),'member');self.assertEqual(self.s.membership('123'),'member');self.bot.api_call.assert_called_once()
        self.s.members.clear();self.bot.api_call.return_value={'ok':True,'result':{'status':'left'}}
        self.assertEqual(self.s.membership('123'),'not_member')

    def test_membership_requires_an_admin_bot(self):
        self.s.admin_checks.clear()
        self.bot.api_call.return_value={'ok':True,'result':{'status':'member'}}
        self.assertEqual(self.s.membership('123'),'unavailable')
        self.assertEqual(self.bot.api_call.call_count,1)
