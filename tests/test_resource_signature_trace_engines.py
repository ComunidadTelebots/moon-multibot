import unittest
import resource_signature_trace_engines as e
class SignatureTraceTests(unittest.TestCase):
 def test_signatures(self):
  funcs=[e.sign_accessible_preferences,e.sign_integration_secrets,e.sign_contextual_responses,e.sign_miniapp_menus,e.sign_bot_statistics,e.sign_ad_preferences,e.sign_processing_queues]
  for i,fn in enumerate(funcs):
   r=fn({"x":1},"k","1234567890123456"); self.assertEqual(r["envelope"]["feature_id"],e.IDS[i]); self.assertTrue(r["signed"])
 def test_traces(self):
  funcs=[e.trace_creator_accounts,e.trace_partner_channels,e.trace_community_campaigns,e.trace_editorial_articles,e.trace_moderated_images,e.trace_user_appeals,e.trace_mtproto_proxies,e.trace_persistent_tasks,e.trace_moderation_rules,e.trace_language_metrics,e.trace_community_translations,e.trace_personal_consents,e.trace_telegram_reactions]
  events=[{"span_id":"root","parent_id":None,"sequence":0,"service":"api","status":"ok"},{"span_id":"child","parent_id":"root","sequence":1,"service":"worker","status":"ok"}]
  for i,fn in enumerate(funcs,7):
   r=fn("trace-1",events); self.assertEqual(r["feature_id"],e.IDS[i]); self.assertTrue(r["complete"] and r["read_only"])
 def test_orphan_detected(self):
  r=e.trace_creator_accounts("t",[{"span_id":"x","parent_id":"missing","sequence":1,"service":"x","status":"error"}]); self.assertFalse(r["complete"]); self.assertEqual(r["orphan_spans"],("x",))
if __name__=="__main__": unittest.main()
