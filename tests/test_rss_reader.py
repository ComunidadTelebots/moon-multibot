import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace
from flask import Flask
from core.personal_rss_runtime import PersonalRssService
from core.personal_rss_engine import plain_summary
from core.rss_reader import source_for, read_entries, share_entry, register_reader_routes, WEBAPP_URL
from tests.test_personal_rss_runtime import DB

class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.s=PersonalRssService(DB(),lambda:[])
        self.s.manager=Mock()
        self.s.manager.list.side_effect=lambda uid: [{'id':'private','url':'https://example.com/feed'}] if uid=='123' else []
        self.source={'id':'news','title':'Source & title','url':'https://example.com/feed'}
        self.catalog=patch('core.rss_reader.CATALOG',[self.source]);self.catalog.start();self.addCleanup(self.catalog.stop)
        self.s.manager.fetch.return_value=[{'id':'entry','title':'<b>Title</b>','url':'https://example.com/story?a=1&b=2','summary':'News'}]
        self.bot=Mock();self.bot.api_call.side_effect=lambda method,args: {'ok':True,'result':{'username':'destination','message_id':42}}
        self.rights=patch('core.rss_reader.channel_bot',return_value=self.bot);self.rights.start();self.addCleanup(self.rights.stop)
    def test_private_source_isolation(self):
        self.assertIsNotNone(source_for(self.s,'123','own:private'))
        self.assertIsNone(source_for(self.s,'999','own:private'))
        with patch('core.rss_reader.channel_bot',return_value=None):
            self.assertIsNone(source_for(self.s,'123','channel:-99:private'))
    def test_summary_and_unsafe_links(self):
        self.assertEqual(plain_summary('<p>Good &amp; safe</p><script>bad()</script><style>bad</style>'), 'Good & safe')
        self.s.manager.fetch.return_value += [{'url':'javascript:alert(1)'},{'url':'https://user:pass@example.com/'},{'url':'https://example.com/'+'x'*2100}]
        _,entries=read_entries(self.s,'0','news');self.assertEqual(len(entries),1)
        self.assertIsNone(self.s.db.get('PERSONAL_RSS_DAILY_0'));self.bot.api_call.assert_not_called()
    def test_share_escapes_html_and_deduplicates(self):
        self.assertEqual(share_entry(self.s,'123','news','entry','-99')[1],200)
        send=[c for c in self.bot.api_call.call_args_list if c.args[0]=='sendMessage']
        self.assertEqual(len(send),1)
        self.assertIn('&lt;b&gt;Title&lt;/b&gt;',send[0].args[1]['text'])
        self.assertEqual(send[0].args[1]['reply_markup']['inline_keyboard'][0][0]['url'],WEBAPP_URL)
        self.assertTrue(share_entry(self.s,'123','news','entry','-99')[0]['already_sent'])
        self.assertEqual(sum(c.args[0]=='sendMessage' for c in self.bot.api_call.call_args_list),1)
    def test_denied_permission_does_not_send(self):
        with patch('core.rss_reader.channel_bot',return_value=None):self.assertEqual(share_entry(self.s,'123','news','entry','-99')[1],403)
        self.bot.api_call.assert_not_called()
    def test_uncertain_send_survives_new_service(self):
        self.bot.api_call.side_effect=lambda method,args: {'ok':False} if method=='sendMessage' else {'ok':True,'result':{}}
        self.assertEqual(share_entry(self.s,'123','news','entry','-99')[1],503)
        restarted=PersonalRssService(self.s.db,lambda:[]);restarted.manager=self.s.manager
        self.assertEqual(share_entry(restarted,'123','news','entry','-99')[1],409)
        self.assertEqual(sum(c.args[0]=='sendMessage' for c in self.bot.api_call.call_args_list),1)
    def test_self_channel_mirror_rejected(self):
        self.s.manager.fetch.return_value[0]['url']='https://t.me/Destination/123'
        self.assertEqual(share_entry(self.s,'123','news','entry','-99')[1],400)
        self.assertFalse(any(c.args[0]=='sendMessage' for c in self.bot.api_call.call_args_list))
    def test_route_identity_auth_and_server_resolved_entry(self):
        app=Flask(__name__)
        register_reader_routes(app,self.s,SimpleNamespace(_verify_init_data=lambda v: {'id':123} if v=='signed' else None),lambda:False)
        client=app.test_client()
        self.assertEqual(client.post('/api/internal/rss/reader/123',json={}).status_code,401)
        self.assertEqual(client.post('/api/public/rss/reader',json={}).status_code,401)
        with patch('core.rss_reader.share_entry',return_value=({'ok':True},200)) as share:
            r=client.post('/api/public/rss/reader',json={'initData':'signed','action':'share','user_id':'999','source_id':'news','entry_id':'entry','channel_id':'-99','text':'injected','url':'https://evil.example'})
            self.assertEqual(r.status_code,200)
            share.assert_called_once_with(self.s,'123','news','entry','-99')
