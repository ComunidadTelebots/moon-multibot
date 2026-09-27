import unittest
from unittest.mock import Mock, patch
from flask import Flask
from types import SimpleNamespace
from core.rss_channels import channel_bot, register_channel_routes
from core.personal_rss_runtime import PersonalRssService
from tests.test_personal_rss_runtime import DB

class ChannelRssTests(unittest.TestCase):
    def setUp(self):
        self.db=DB();self.db.set('CHATS_1:secret',['123','-99'])
        self.bot=Mock(token='1:secret')
        self.admin=True;self.bot_rights=True
        def api(method,args):
            if method=='getChat':return {'ok':True,'result':{'type':'channel'}}
            if args['user_id']=='1':return {'ok':True,'result':{'status':'administrator','can_post_messages':self.bot_rights}}
            return {'ok':True,'result':{'status':'administrator' if self.admin else 'member','can_post_messages':self.admin}}
        self.bot.api_call.side_effect=api
        self.s=PersonalRssService(self.db,lambda:[self.bot]); self.s.action=Mock(return_value=({'ok':True,'feeds':[]},200))
        public=SimpleNamespace(_verify_init_data=lambda value:{'id':123} if value=='signed' else None,_channel_stats=Mock())
        public._channel_stats.get_user_channels.return_value=[{'chat_id':'-99','ctype':'channel','name':'Canal'}]
        app=Flask(__name__);register_channel_routes(app,self.s,public,lambda:False);self.client=app.test_client()
    def test_live_permissions(self):
        self.assertIs(channel_bot(self.s,'123','-99'),self.bot)
        self.admin=False;self.assertIsNone(channel_bot(self.s,'123','-99'))
        self.admin=True;self.bot_rights=False;self.assertIsNone(channel_bot(self.s,'123','-99'))
    def test_unsigned_hub_and_internal_calls_rejected(self):
        self.assertEqual(self.client.post('/api/public/rss/channel',json={'chat_id':'-99'}).status_code,401)
        self.assertEqual(self.client.get('/api/internal/rss/channels/123/-99').status_code,401)
        self.s.action.assert_not_called()
    def test_hub_uses_signed_actor_and_only_selected_channel(self):
        r=self.client.post('/api/public/rss/channel',json={'initData':'signed','chat_id':'-99','user_id':'999','action':'toggle','feed_id':'one','enabled':True})
        self.assertEqual(r.status_code,200)
        self.s.action.assert_called_once_with('-99',{'action':'toggle','feed_id':'one','enabled':True},'123')
        self.assertEqual(self.db.get('PERSONAL_RSS_CHANNEL_OWNER_-99'),'123')
    def test_removed_admin_cannot_change_subscription(self):
        self.admin=False
        self.assertEqual(self.client.post('/api/public/rss/channel',json={'initData':'signed','chat_id':'-99','action':'delete'}).status_code,403)
        self.s.action.assert_not_called()
    def test_unknown_channel_rejected(self):
        self.assertIsNone(channel_bot(self.s,'123','-88'))
        self.bot.api_call.assert_not_called()

    def test_scheduled_channel_delivery_rechecks_admin_and_has_no_private_quota(self):
        self.db.set('GROUP_RSS_GROUPS',['-99']);self.db.set('PERSONAL_RSS_CHANNEL_OWNER_-99','123')
        self.s.manager=Mock();self.s.manager.list.return_value=[{'id':'one','enabled':True}]
        self.s.manager.poll.return_value=[{'id':'entry','feed_id':'one','title':'Title','url':'https://example.com'}]
        self.bot.send_msg.return_value={'ok':True}
        with patch('core.personal_rss_runtime.time.sleep'):
            self.s.cycle()
        self.bot.send_msg.assert_called_once_with('-99','Title\nhttps://example.com',parse_mode=None)
        self.assertIsNone(self.db.get('PERSONAL_RSS_DAILY_-99'))
        self.admin=False
        self.s.cycle();self.bot.send_msg.assert_called_once()

    def test_own_channel_mirror_is_rejected(self):
        original=self.bot.api_call.side_effect
        self.bot.api_call.side_effect=lambda method,args: {'ok':True,'result':{'type':'channel','username':'TodoSobreAllTech'}} if method=='getChat' else original(method,args)
        r=self.client.post('/api/public/rss/channel',json={'initData':'signed','chat_id':'-99','action':'add','url':'https://rss.app/feeds/v1.1/VIGykitWBlIEm69s.json'})
        self.assertEqual(r.status_code,400);self.s.action.assert_not_called()
