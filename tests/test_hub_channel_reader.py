import unittest
from core.hub_channel_reader import normalize_posts

class ReaderTests(unittest.TestCase):
    def test_only_alltech_public_posts_are_exposed(self):
        urls=['https://t.me/TodoSobreAllTech/123','https://t.me/AnotherChannel/1','javascript:alert(1)','https://t.me.evil.test/TodoSobreAllTech/123','https://t.me/TodoSobreAllTech/not-a-post']
        rows=normalize_posts({'messages':[{'url':u,'text':'<script>not markup</script>','token':'secret'} for u in urls]})
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['id'],'123')
        self.assertNotIn('token',rows[0])
    def test_limits_and_malformed_payload(self):
        row={'url':'https://t.me/TodoSobreAllTech/1','text':'x'*7000}
        posts=normalize_posts({'messages':[row]*80})
        self.assertEqual(len(posts),40)
        self.assertEqual(len(posts[0]['text']),5000)
        with self.assertRaises(ValueError):normalize_posts([])
if __name__=='__main__':unittest.main()
