import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from flask import Flask, Blueprint
from core.rss_subscriptions import aggregate_rss, install_rss_routes

class RssSubscriptionsTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.db.get.side_effect = lambda key, default=None: {"CHATS_secret": [123], "GROUP_RSS_GROUPS": [123, -99]}.get(key, default)
        self.action = Mock(return_value=({"ok": True, "feeds": []}, 200))
        self.manager = Mock()
        self.manager.list.side_effect = lambda cid: [{"url": "https://example.com/rss", "title": "News", "published_count": 4 if str(cid)=='123' else 7, "enabled": True, "error_count": 1}]
        self.allowed = True
        app=Flask(__name__); bp=Blueprint('rss',__name__)
        install_rss_routes(bp, lambda:self.allowed, lambda:self.manager, self.action, lambda:self.db, lambda:[SimpleNamespace(token='secret')])
        app.register_blueprint(bp); self.client=app.test_client()
    def test_requires_internal_auth(self):
        self.allowed=False
        for path in ['/api/internal/rss/activity','/api/internal/rss/users/123']:
            self.assertEqual(self.client.get(path).status_code,401)
        self.action.assert_not_called()
    def test_requires_known_private_chat(self):
        self.assertEqual(self.client.get('/api/internal/rss/users/456').status_code,409)
        self.assertEqual(self.client.get('/api/internal/rss/users/-99').status_code,400)
        self.action.assert_not_called()
    def test_allowlist_and_owner(self):
        r=self.client.post('/api/internal/rss/users/123',json={'action':'add','url':'https://example.com/rss','chat_id':'456','message_thread_id':1})
        self.assertEqual(r.status_code,200)
        self.action.assert_called_once_with('123',{'action':'add','url':'https://example.com/rss'},'123')
    def test_rejects_actions_and_invalid_toggle(self):
        for body in [{'action':'run_now'},{'action':'toggle','enabled':'false'},['add']]:
            self.assertEqual(self.client.post('/api/internal/rss/users/123',json=body).status_code,400)
        self.action.assert_not_called()
    def test_real_aggregates(self):
        result=aggregate_rss(self.manager,self.db)
        self.assertEqual(result['totals']['published'],11)
        self.assertEqual(result['sources'][0]['subscriptions'],2)
        self.assertEqual(result['recipients'][0]['id'],'-99')
        self.assertNotIn('url',result['sources'][0])
    def test_statistics_cache(self):
        for _ in range(2): self.assertEqual(self.client.get('/api/internal/rss/activity').status_code,200)
        self.assertEqual(self.manager.list.call_count,2)
