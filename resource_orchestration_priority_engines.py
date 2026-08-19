"""Event orchestration decisions and adaptive priorities for Moonbot resources."""
IDS=tuple(f"future-{n}" for n in (3302,3305,3308,3311,3314,3317,3320,3323,3326,3329,3332,3335,3338,3341,3344,3347,3350,3353,3356,3359))
def _orchestrate(fid,resource,event,expected,plans):
 if not isinstance(event,dict) or event.get("type") not in expected: raise ValueError("Evento no soportado")
 plan=plans[event["type"]]; return {"feature_id":fid,"resource":resource,"event_type":event["type"],"correlation_id":str(event.get("id") or ""),"planned_steps":[{"order":i+1,"action":x} for i,x in enumerate(plan)],"executed":False,"idempotency_required":True}
def orchestrate_temporary_roles(e): return _orchestrate(IDS[0],"temporary_roles",e,{"role_expiring","role_granted"},{"role_expiring":["notify_owner","request_review"],"role_granted":["record_audit","sync_permissions"]})
def orchestrate_managed_groups(e): return _orchestrate(IDS[1],"managed_groups",e,{"group_added","permission_lost"},{"group_added":["inspect_permissions","sync_commands"],"permission_lost":["alert_admin","degrade_capabilities"]})
def orchestrate_scheduled_messages(e): return _orchestrate(IDS[2],"scheduled_messages",e,{"message_due","delivery_failed"},{"message_due":["check_quiet_hours","enqueue_delivery"],"delivery_failed":["record_attempt","schedule_retry"]})
def orchestrate_rss_feeds(e): return _orchestrate(IDS[3],"rss_feeds",e,{"entry_found","feed_failed"},{"entry_found":["apply_filters","prepare_preview"],"feed_failed":["increment_failures","apply_backoff"]})
def orchestrate_telegram_videos(e): return _orchestrate(IDS[4],"telegram_videos",e,{"video_received","scan_complete"},{"video_received":["validate_size","request_scan"],"scan_complete":["record_verdict","request_review"]})
def orchestrate_blocklists(e): return _orchestrate(IDS[5],"blocklists",e,{"list_updated","match_found"},{"list_updated":["validate_entries","publish_version"],"match_found":["record_match","request_moderation"]})
def orchestrate_mandatory_subscriptions(e): return _orchestrate(IDS[6],"mandatory_subscriptions",e,{"member_joined","subscription_verified"},{"member_joined":["check_channels","restrict_pending"],"subscription_verified":["restore_permissions","record_verification"]})
def orchestrate_signed_webhooks(e): return _orchestrate(IDS[7],"signed_webhooks",e,{"delivery_due","signature_rejected"},{"delivery_due":["sign_payload","enqueue_request"],"signature_rejected":["record_security_event","pause_endpoint"]})
def orchestrate_quiet_hours(e): return _orchestrate(IDS[8],"quiet_hours",e,{"quiet_started","quiet_ended"},{"quiet_started":["defer_eligible_jobs","record_transition"],"quiet_ended":["release_deferred_jobs","record_transition"]})
def orchestrate_correlated_incidents(e): return _orchestrate(IDS[9],"correlated_incidents",e,{"signal_linked","incident_resolved"},{"signal_linked":["recompute_severity","notify_reviewers"],"incident_resolved":["close_signals","archive_evidence"]})
def orchestrate_accessible_preferences(e): return _orchestrate(IDS[10],"accessible_preferences",e,{"preference_changed","profile_loaded"},{"preference_changed":["validate_preferences","sync_clients"],"profile_loaded":["resolve_effective_values","render_preview"]})
def orchestrate_integration_secrets(e): return _orchestrate(IDS[11],"integration_secrets",e,{"rotation_due","secret_compromised"},{"rotation_due":["create_version","request_activation"],"secret_compromised":["disable_version","alert_owner"]})
def orchestrate_contextual_responses(e): return _orchestrate(IDS[12],"contextual_responses",e,{"intent_detected","reply_rejected"},{"intent_detected":["apply_confidence_policy","draft_reply"],"reply_rejected":["record_feedback","adjust_review_queue"]})
def orchestrate_miniapp_menus(e): return _orchestrate(IDS[13],"miniapp_menus",e,{"role_changed","menu_published"},{"role_changed":["resolve_visibility","build_menu"],"menu_published":["record_version","invalidate_cache"]})
def orchestrate_bot_statistics(e): return _orchestrate(IDS[14],"bot_statistics",e,{"window_closed","threshold_crossed"},{"window_closed":["aggregate_counters","store_snapshot"],"threshold_crossed":["create_alert","attach_metrics"]})
def orchestrate_ad_preferences(e): return _orchestrate(IDS[15],"ad_preferences",e,{"consent_changed","frequency_reached"},{"consent_changed":["update_eligibility","record_consent"],"frequency_reached":["suppress_placement","set_reset_time"]})
def orchestrate_processing_queues(e): return _orchestrate(IDS[16],"processing_queues",e,{"task_queued","worker_failed"},{"task_queued":["calculate_priority","assign_partition"],"worker_failed":["release_lease","schedule_retry"]})
def _priority(fid,resource,item,weights):
 if not isinstance(item,dict): raise ValueError("Elemento requerido")
 components=[]; total=0
 for field,weight in weights.items():
  value=float(item.get(field,0)); contribution=value*weight; components.append({"field":field,"value":value,"weight":weight,"contribution":round(contribution,3)}); total+=contribution
 return {"feature_id":fid,"resource":resource,"priority":round(max(0,min(total,100)),2),"components":components,"adaptive":True,"automatic_action":False}
def prioritize_creator_account(x): return _priority(IDS[17],"creator_accounts",x,{"risk":.5,"pending_reviews":8,"days_inactive":.3})
def prioritize_associated_channel(x): return _priority(IDS[18],"associated_channels",x,{"delivery_failures":10,"permission_gaps":15,"stale_hours":.2})
def prioritize_community_campaign(x): return _priority(IDS[19],"community_campaigns",x,{"hours_to_send":-1,"pending_approval":30,"delivery_risk":.5})
