"""Versionable manifest for Moonbot catalog sublot 2."""
import resource_drift_impact_engines as e
APIS=["drift_editorial_articles","drift_moderated_images","drift_user_appeals","drift_mtproto_proxies","drift_persistent_tasks","drift_moderation_rules","drift_language_metrics","drift_community_translations","drift_personal_consents","drift_telegram_reactions","drift_master_panels","drift_channel_directories","drift_external_links","impact_admin_sessions","impact_community_profiles","impact_telegram_communities","impact_house_ads","impact_voice_notes","impact_suspicious_files","impact_captcha_decisions"]
MANIFEST=[{"release_channel": "prealfa", "id":fid,"module":"resource_drift_impact_engines.py","api":api,"capability":api.replace("_"," "),"test":"tests/test_resource_drift_impact_engines.py","preflight":"Moonbot catalog proposed; rg found no matching resource schema and decision"} for fid,api in zip(e.IDS,APIS)]
assert len(MANIFEST)==20 and len({x["api"] for x in MANIFEST})==20
