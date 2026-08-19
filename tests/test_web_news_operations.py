import unittest
from core import web_news_operations as f
from core.web_news_operations_manifest import FEATURES
N="2026-07-30T10:00:00Z"
class WebNewsOperationsTests(unittest.TestCase):
 def test_0071(self): self.assertFalse(f.news_permission({},"e","publish","review")["allowed"])
 def test_0072(self): self.assertTrue(f.news_template("{title} {summary} {source_url}",{"title":"T","summary":"S","source_url":"https://e.com"})["draft"])
 def test_0073(self): self.assertFalse(f.news_bulk_plan([{"id":"a","status":"draft"}],"review")["applied"])
 def test_0074(self): self.assertFalse(f.news_calendar([{"article_id":"a","publish_at":N}],"Europe/Madrid")["publishes_automatically"])
 def test_0075(self): self.assertFalse(f.news_privacy({"title":"T","author_email":"x"})["pii_included"])
 def test_0076(self): self.assertIn("sources",f.news_diagnostics({"title":"T","slug":"t","summary":"short","sources":[]})["blocking"])
 def test_0077(self): self.assertEqual(f.news_recommendations({"sources":[]},{})[0]["action"],"add_source")
 def test_0078(self): self.assertEqual(f.news_approval({"status":"review","author_id":"a"},"b","publish",N)["status"],"published")
 def test_0079(self): self.assertEqual(f.news_comment([],{"id":"c","anchor":"body","text":"ok","author":"e"})[0]["resolved"],False)
 def test_0080(self):
  e={"id":"x","type":"view","value":2}; s=f.news_metric({},e); self.assertEqual(f.news_metric(s,e),s)
 def test_0081(self): self.assertTrue(f.news_accessibility({"reading_level":"plain","image_alt_required":True})["color_independent"])
 def test_0082(self): self.assertFalse(f.news_webhook("https://e.com","article.published",{"id":"a","slug":"a","status":"published"},"0123456789abcdef")["sent"])
 def test_0083(self): self.assertTrue(f.news_anomaly([10,10,100])["anomaly"])
 def test_0084(self): self.assertEqual(f.news_learning(["sources"],"writer")["next"],"style")
 def test_0085(self): self.assertEqual(f.news_language("en",{"en":"T","es":"T"})["fallback"],"es")
 def test_0086(self): self.assertFalse(f.news_compact({"title":"T","body":"secret"},"headline")["body_included"])
 def test_0087(self): self.assertFalse(f.news_recovery({"id":"a","title":"N"},{"title":"O"},["title"])["applied"])
 def test_0088(self): self.assertFalse(f.news_report({"frequency":"daily","format":"json"},{"views":2})["delivered"])
 def test_0089(self): self.assertEqual(f.news_sandbox({"status":"draft"},{"type":"submit_review"})["effects"],[])
 def test_0090(self): self.assertFalse(f.news_connector({"id":"a","title":"T","token":"x"},"rss")["credentials_included"])
 def test_manifest(self):
  self.assertEqual(len(FEATURES),20);self.assertEqual(len({x["api"] for x in FEATURES}),20)
  for x in FEATURES:self.assertTrue(hasattr(f,x["api"]))
if __name__=="__main__":unittest.main()
