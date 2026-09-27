import json
import unittest
from unittest.mock import patch
from core.personal_rss_engine import PersonalRssManager

class JsonFeedTests(unittest.TestCase):
    def parse(self,items):
        return PersonalRssManager.parse_json_feed(json.dumps({'version':'https://jsonfeed.org/version/1.1','items':items}).encode(),'https://rss.app/feed.json')
    def test_json_feed_external_links_and_stable_ids(self):
        item={'id':'x','title':'News','url':'https://mirror.example/x','external_url':'https://original.example/x'}
        first=self.parse([item]);self.assertEqual(first[0]['url'],'https://original.example/x')
        self.assertEqual(first,self.parse([item]));self.assertNotIn('content_html',first[0])
    def test_unsafe_or_missing_links_are_skipped(self):
        self.assertEqual(self.parse([{'url':'javascript:alert(1)'},{'url':'https://user:pass@example.com/a'}, {'id':'empty'}]),[])
    def test_bounded_items_and_title(self):
        result=self.parse([{'id':str(i),'url':'https://example.com/'+str(i),'title':'a'*1000} for i in range(100)])
        self.assertEqual(len(result),50);self.assertEqual(len(result[0]['title']),300)
    def test_rejects_non_feed_json(self):
        for body in [b'[]',b'{"items":[]}',b'{"version":"https://jsonfeed.org/version/1.1","items":{}}']:
            with self.assertRaises(ValueError): PersonalRssManager.parse_json_feed(body,'https://example.com/feed')
    def test_rebinding_to_private_address_is_rejected(self):
        public=[(2,1,6,'',('8.8.8.8',443))];private=[(2,1,6,'',('127.0.0.1',443))]
        with patch('core.personal_rss_engine.socket.getaddrinfo',side_effect=[public,private]),patch('core.personal_rss_engine.http.client.HTTPSConnection') as connection:
            with self.assertRaises(ValueError):PersonalRssManager(None).fetch('https://example.com/feed')
            connection.assert_not_called()
