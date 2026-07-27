import time

from flask import Blueprint, jsonify, request
from community_members import CommunityMembers
from community_engagement import CommunityEngagement
from group_administration import GroupAdministration
from roadmap_engine import RoadmapEngine
from horizon_full import FullHorizonSuite

bp = Blueprint("users_routes", __name__)

_check_jwt = None
_db = None
_ban_manager = None
_add_audit_log = None
_add_web_log = None
_get_bot_for_chat = None
_iter_known_group_targets = None
_get_global_media_list = None
_get_global_user_stats = None


def setup(
    check_jwt,
    db,
    ban_manager,
    add_audit_log,
    add_web_log,
    get_bot_for_chat,
    iter_known_group_targets,
    get_global_media_list,
    get_global_user_stats,
):
    global _check_jwt, _db, _ban_manager, _add_audit_log, _add_web_log
    global _get_bot_for_chat, _iter_known_group_targets, _get_global_media_list, _get_global_user_stats
    _check_jwt = check_jwt
    _db = db
    _ban_manager = ban_manager
    _add_audit_log = add_audit_log
    _add_web_log = add_web_log
    _get_bot_for_chat = get_bot_for_chat
    _iter_known_group_targets = iter_known_group_targets
    _get_global_media_list = get_global_media_list
    _get_global_user_stats = get_global_user_stats
    return bp


@bp.route("/api/media")
def web_media():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "media": _get_global_media_list()[-50:]})


@bp.route("/api/stats/users")
def web_user_stats():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    global_user_stats = _get_global_user_stats()
    sorted_u = sorted(global_user_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:10]
    return jsonify({"ok": True, "users": [{"id": k, "name": v["name"], "count": v["count"]} for k, v in sorted_u]})


@bp.route("/api/users/ban", methods=["POST"])
def web_user_ban():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    data = request.json or {}
    u = str(data.get("uid", "")).strip()
    cid = data.get("cid")
    reason = data.get("reason", "Manual ban from web")
    scope = data.get("scope") or ("local" if cid else "global")
    if not u:
        return jsonify({"ok": False, "msg": "UID requerido"}), 400
    if scope == "local":
        if not cid:
            return jsonify({"ok": False, "msg": "CID requerido para ban local"}), 400
        _ban_manager.ban_local_user(cid, u, reason=reason, source="web_manual")
        audit_msg = f"Usuario {u} baneado localmente en {cid}. Razon: {reason}"
    else:
        _ban_manager.ban_user(u, reason=reason, source="web_manual")
        audit_msg = f"Usuario {u} baneado globalmente. Razon: {reason}"
    _add_audit_log(audit_msg)
    bot = _get_bot_for_chat(cid) if cid else None
    telegram_result = None
    telegram_results = []
    if cid and bot:
        telegram_result = bot.kick_user(cid, u)
        telegram_results.append({"cid": str(cid), "ok": telegram_result.get("ok"), "description": telegram_result.get("description")})
        if telegram_result.get("ok"):
            _add_web_log("SECURITY", f"Usuario {u} expulsado de {cid} ({scope}).")
        else:
            _add_web_log("ERROR", f"No se pudo expulsar a {u} de {cid}: {telegram_result.get('description')}")
    elif scope == "global":
        for target_bot, target_cid in _iter_known_group_targets():
            res = target_bot.kick_user(target_cid, u)
            telegram_results.append({"cid": target_cid, "ok": res.get("ok"), "description": res.get("description")})
        if telegram_results:
            ok_count = len([r for r in telegram_results if r.get("ok")])
            _add_web_log("SECURITY", f"Ban global de {u} propagado a {ok_count}/{len(telegram_results)} grupos conocidos.")
    return jsonify({"ok": True, "scope": scope, "telegram": telegram_result, "telegram_results": telegram_results, "message": audit_msg})


@bp.route("/api/ping")
def web_ping():
    return jsonify({"ok": True, "status": "online", "time": time.time()})


@bp.route("/api/users/bans", methods=["GET"])
def web_get_bans():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    cid = request.args.get("cid")
    bans_data = _ban_manager.get_local_bans(cid) if cid else _ban_manager.get_all_bans()
    return jsonify({"ok": True, "scope": "local" if cid else "global", "cid": cid, "total": len(bans_data.get("users", [])), "bans": bans_data.get("users", [])})


@bp.route("/api/users/bans/stats", methods=["GET"])
def web_get_ban_stats():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, **_ban_manager.get_ban_stats()})


@bp.route("/api/users/bans/history", methods=["GET"])
def web_get_ban_history():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    limit = request.args.get("limit", 50, type=int)
    history = _ban_manager.get_ban_history(limit)
    return jsonify({"ok": True, "history": history})


@bp.route("/api/users/unban", methods=["POST"])
def web_user_unban():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    data = request.json or {}
    u = str(data.get("uid", "")).strip()
    cid = data.get("cid")
    scope = data.get("scope") or ("local" if cid else "global")
    if not u:
        return jsonify({"ok": False, "message": "UID requerido"}), 400
    result = _ban_manager.unban_local_user(cid, u) if scope == "local" and cid else _ban_manager.unban_user(u)
    telegram_result = None
    telegram_results = []
    if cid:
        bot = _get_bot_for_chat(cid)
        if bot:
            telegram_result = bot.api_call("unbanChatMember", {"chat_id": cid, "user_id": u})
            telegram_results.append({"cid": str(cid), "ok": telegram_result.get("ok"), "description": telegram_result.get("description")})
    elif scope == "global":
        for target_bot, target_cid in _iter_known_group_targets():
            res = target_bot.api_call("unbanChatMember", {"chat_id": target_cid, "user_id": u})
            telegram_results.append({"cid": target_cid, "ok": res.get("ok"), "description": res.get("description")})
    if result:
        _add_audit_log(f"Usuario {u} desbaneado desde web ({scope})")
        _add_web_log("SECURITY", f"Usuario {u} desbaneado ({scope})")
        return jsonify({"ok": True, "scope": scope, "telegram": telegram_result, "telegram_results": telegram_results, "message": "Usuario desbaneado"})
    return jsonify({"ok": False, "message": "Usuario no estaba baneado"})


@bp.route("/api/users/notes", methods=["POST"])
def web_user_notes():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    d = request.json
    uid, note = str(d.get("uid")), d.get("note", "")
    global_user_stats = _get_global_user_stats()
    if uid in global_user_stats:
        global_user_stats[uid]["notes"] = note
    return jsonify({"ok": True})


@bp.route("/api/stats/heatmap")
def web_heatmap():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    history = _db.get("GLOBAL_HISTORY", [])
    counts = [0] * 24
    for m in history:
        try:
            hour = int(m.get("time", "00:00").split(":")[0])
            if 0 <= hour < 24:
                counts[hour] += 1
        except Exception:
            pass
    return jsonify({"ok": True, "heatmap": counts})


@bp.route("/api/users/community")
def web_community_members():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    manager = CommunityMembers(_db)
    profiles = _db.get("COMMUNITY_PROFILES", {})
    profiles = profiles if isinstance(profiles, dict) else {}
    return jsonify({"ok": True, "profiles": [manager.profile(uid) for uid in profiles],
                    "role_requests": manager.role_requests(request.args.get("status"))})


@bp.route("/api/users/community/xp", methods=["POST"])
def web_community_xp():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body = request.json or {}
    return jsonify({"ok": True, "profile": CommunityMembers(_db).add_xp(
        body.get("user_id"), body.get("amount", 0), body.get("reason", "admin")
    )})


@bp.route("/api/users/community/role-request/resolve", methods=["POST"])
def web_community_role_resolve():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body = request.json or {}
    if body.get("decision") not in ("approved", "rejected"):
        return jsonify({"ok": False, "error": "decisión inválida"}), 400
    item = CommunityMembers(_db).resolve_role(body.get("request_id"), body["decision"], "master_web")
    return jsonify({"ok": bool(item), "request": item}), 200 if item else 404


@bp.route("/api/users/community/recognize", methods=["POST"])
def web_community_recognize():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, **CommunityMembers(_db).weekly_recognition((request.json or {}).get("limit", 5))})


@bp.route("/api/users/community/verify", methods=["POST"])
def web_community_verify():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body = request.json or {}
    return jsonify({"ok": True, "profile": CommunityMembers(_db).verify(
        body.get("user_id"), body.get("verified", True)
    )})


@bp.route("/api/users/engagement")
def web_engagement():
    if not _check_jwt(request): return jsonify({"ok": False}), 401
    service = CommunityEngagement(_db)
    return jsonify({"ok": True, "events": service.events(), "surveys": service.surveys(),
                    "inbox": list(reversed(service._rows(_db, "COMMUNITY_ANONYMOUS_INBOX"))),
                    "mentors": _db.get("COMMUNITY_MENTORS", {}),
                    "matches": list(reversed(service._rows(_db, "COMMUNITY_MENTOR_MATCHES"))),
                    "challenges": list(reversed(service._rows(_db, "COMMUNITY_CHALLENGES")))})


@bp.route("/api/users/engagement/action", methods=["POST"])
def web_engagement_action():
    if not _check_jwt(request): return jsonify({"ok": False}), 401
    body, service = request.json or {}, CommunityEngagement(_db)
    action = body.get("action")
    try:
        if action == "event_create": result = service.create_event(body.get("title"), body.get("starts_at"), body.get("capacity", 0), body.get("description", ""), body.get("kind", "event"))
        elif action == "survey_create": result = service.create_survey(body.get("title"), body.get("options") or [], body.get("anonymous", True), body.get("closes_at"))
        elif action == "challenge_create": result = service.create_challenge(body.get("title"), body.get("target", 1), body.get("ends_at"))
        elif action == "draw": result = service.draw(body.get("event_id"), body.get("winners", 1), body.get("seed"))
        elif action == "event_stats": result = service.event_stats(body.get("event_id"))
        elif action == "checkin": result = service.checkin(body.get("event_id"), body.get("user_id"))
        elif action == "question_moderate": result = service.moderate_question(body.get("event_id"), body.get("question_id"), body.get("status"))
        elif action == "contest_score": result = service.score_contest(body.get("event_id"), body.get("submission_id"), "master_web", body.get("score"))
        elif action == "agenda": result = service.agenda_ics()
        else: return jsonify({"ok": False, "error": "acción inválida"}), 400
        return jsonify({"ok": bool(result), "result": result}), 200 if result else 404
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@bp.route("/api/users/group-administration")
def web_group_administration():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, **GroupAdministration(_db).snapshot()})


@bp.route("/api/users/group-administration/action", methods=["POST"])
def web_group_administration_action():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body, service = request.json or {}, GroupAdministration(_db)
    action, actor = body.get("action"), "master_web"
    try:
        if action == "setup":
            result = service.setup(body.get("group_id"), body.get("community_type"), actor)
        elif action == "update":
            result = service.update(body.get("group_id"), body.get("patch") or {}, actor)
        elif action == "compare":
            result = service.compare(body.get("group_ids") or [])
        elif action == "sync":
            result = service.sync(body.get("source_id"), body.get("target_ids") or [], body.get("fields") or [], actor)
        elif action == "history":
            result = service.history(body.get("group_id"))
        elif action == "restore":
            result = service.restore(body.get("group_id"), body.get("version"), actor)
        elif action == "approve":
            result = service.approve(body.get("request_id"), body.get("actor") or actor)
        elif action == "delegate":
            result = service.delegate(body.get("group_id"), body.get("user_id"), body.get("permissions") or [], body.get("expires_at"), actor)
        elif action == "calendar":
            result = service.calendar_action(body.get("group_id"), body.get("scheduled_action"), body.get("execute_at"), body.get("payload"))
        elif action == "hours":
            result = service.set_hours(body.get("group_id"), body.get("timezone", "Europe/Madrid"), body.get("schedule") or {}, actor)
        elif action == "permission_audit":
            result = service.permission_audit(body.get("group_id"), body.get("actual") or {}, body.get("required"))
        else:
            return jsonify({"ok": False, "error": "acción inválida"}), 400
        return jsonify({"ok": bool(result), "result": result}), 200 if result else 404
    except (TypeError, ValueError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@bp.route("/api/users/roadmap")
def web_roadmap_snapshot():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, **RoadmapEngine(_db).snapshot()})


@bp.route("/api/users/horizon-completion")
def web_horizon_completion_catalog():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    service = FullHorizonSuite(_db)
    catalog = service.catalog()
    return jsonify({"ok": True, "features": catalog, "total": len(catalog),
                    "audit": service.audit()[-100:]})


@bp.route("/api/users/horizon/<slug>", methods=["GET", "POST", "PUT", "DELETE"])
def web_horizon_feature(slug):
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    service = FullHorizonSuite(_db)
    feature = service.describe(slug)
    if not feature:
        return jsonify({"ok": False, "error": "feature_not_found"}), 404
    if not str(slug).startswith("future-") and request.method != "POST":
        if request.method == "GET":
            return jsonify({"ok": True, "feature": feature})
        return jsonify({"ok": False, "error": "operation_not_supported_for_legacy_feature"}), 405
    payload = request.json if request.is_json else request.args.to_dict()
    payload = payload if isinstance(payload, dict) else {}
    operations = {"GET": "status", "POST": payload.get("operation", "run"),
                  "PUT": "configure", "DELETE": "rollback"}
    try:
        result = service.execute(slug, {**payload, "operation": operations[request.method]})
        return jsonify({"ok": True, "slug": slug, "operation": operations[request.method], "result": result})
    except (TypeError, ValueError, KeyError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400


@bp.route("/api/users/rich-message", methods=["POST"])
def web_send_rich_message():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body = request.json or {}
    group_id = str(body.get("group_id") or "").strip()
    markdown = str(body.get("markdown") or "")
    if not group_id or not markdown:
        return jsonify({"ok": False, "error": "group_id y markdown son obligatorios"}), 400
    bot = next(
        (candidate for candidate, target_id in _iter_known_group_targets()
         if str(target_id) == group_id),
        None,
    )
    if not bot:
        return jsonify({"ok": False, "error": "no hay un bot disponible para ese grupo"}), 404
    result = bot.send_rich_message(
        group_id, markdown=markdown,
        skip_entity_detection=bool(body.get("skip_entity_detection")),
        fallback_text=markdown,
    )
    _add_audit_log(f"Rich Markdown enviado a {group_id}: ok={bool(result.get('ok'))}")
    return jsonify(result), 200 if result.get("ok") else 400


@bp.route("/api/users/roadmap/action", methods=["POST"])
def web_roadmap_action():
    if not _check_jwt(request):
        return jsonify({"ok": False}), 401
    body, service = request.json or {}, RoadmapEngine(_db)
    action, data = body.get("action"), body.get("data") or {}
    handlers = {
        "raid_signal": lambda: service.raid_signal(data.get("group_id"), data.get("joins", 0), data.get("messages", 0), data.get("unique_users", 0), data.get("window", 60)),
        "quarantine": lambda: service.quarantine_decision(data.get("user_id"), data.get("reputation", 0), data.get("signals")),
        "shared_recurrence": lambda: service.shared_recurrence(data.get("user_id"), data.get("requesting_group"), data.get("authorized_groups") or []),
        "conversation_escalation": lambda: service.conversation_escalation(data.get("group_id"), data.get("samples") or [], data.get("window_seconds", 300)),
        "mediator": lambda: service.mediator_session(data.get("group_id"), data.get("operation"), data.get("user_id"), data.get("statement")),
        "domain_quarantine": lambda: service.domain_quarantine(data.get("url"), data.get("domain_age_days"), data.get("trusted_domains") or [], data.get("minimum_age_days", 30)),
        "peer_review": lambda: service.peer_review(data.get("operation"), data.get("case_id"), data.get("reviewer_id"), data.get("verdict"), data.get("payload"), data.get("quorum", 3)),
        "rule_impact": lambda: service.rule_impact_simulation(data.get("group_id"), data.get("rule") or {}, data.get("samples") or []),
        "coordinated_brigade": lambda: service.coordinated_brigade(data.get("events") or [], data.get("minimum_groups", 2), data.get("minimum_users", 3)),
        "reputation_passport": lambda: service.reputation_passport(data.get("user_id"), data.get("metrics") or {}, data.get("consent", False)),
        "voice_clone_risk": lambda: service.voice_clone_risk(data.get("features") or {}),
        "incident_timeline": lambda: service.incident_timeline(data.get("group_id"), data.get("operation", "list"), data.get("event")),
        "evidence_chain": lambda: service.evidence_chain(data.get("case_id"), data.get("operation", "append"), data.get("evidence")),
        "assembly": lambda: service.assembly(data.get("group_id"), data.get("operation"), data.get("assembly_id"), data.get("actor_id"), data),
        "participatory_budget": lambda: service.participatory_budget(data.get("group_id"), data.get("operation"), data.get("budget_id"), data.get("user_id"), data),
        "interest_circle": lambda: service.interest_circle(data.get("group_id"), data.get("operation"), data.get("circle_id"), data.get("user_id"), data),
        "time_bank": lambda: service.time_bank(data.get("group_id"), data.get("operation"), data.get("user_id"), data.get("target_id"), data.get("hours", 0), data.get("note", "")),
        "welcome_round": lambda: service.welcome_round(data.get("group_id"), data.get("member_id"), data.get("hosts") or [], data.get("capacity", 3)),
        "collaborative_mission": lambda: service.collaborative_mission(data.get("operation", "create"), data.get("group_ids"), data.get("mission_id"), data.get("user_id"), data.get("title", ""), data.get("target", 1), data.get("progress", 0)),
        "invisible_contributions": lambda: service.invisible_contributions(data.get("group_id"), data.get("events") or []),
        "social_health": lambda: service.social_health(data.get("group_id"), data.get("metrics") or {}),
        "admin_relay": lambda: service.admin_relay(data.get("group_id"), data.get("operation", "create"), data.get("outgoing_id"), data.get("incoming_id"), data.get("starts_at"), data.get("ends_at"), data.get("relay_id")),
        "annual_memory": lambda: service.annual_memory(data.get("group_id"), data.get("year"), data.get("highlights"), data.get("metrics"), data.get("contributors")),
        "editorial_series": lambda: service.editorial_series(data.get("operation", "create"), data.get("series_id"), data.get("title", ""), data.get("description", ""), data.get("content_id"), data.get("position")),
        "content_reuse": lambda: service.content_reuse_candidates(data.get("items") or [], data.get("minimum_age_days", 30), data.get("limit", 20)),
        "silence_calendar": lambda: service.silence_calendar(data.get("group_id"), data.get("operation", "check"), data.get("starts_at"), data.get("ends_at"), data.get("reason", ""), data.get("window_id"), data.get("check_at")),
        "headline_comparison": lambda: service.compare_headlines(data.get("headlines") or []),
        "public_announcement": lambda: service.public_announcement_version(data.get("operation", "publish"), data.get("announcement_id"), data.get("title", ""), data.get("body", ""), data.get("correction_note", ""), data.get("actor_id")),
        "horizon_feature": lambda: FullHorizonSuite(_db).execute(data.get("slug"), data.get("payload") or {}),
        "impersonation": lambda: service.impersonation_check(data.get("candidate") or {}, data.get("administrators") or []),
        "link_chain": lambda: service.link_chain(data.get("url"), data.get("hops")),
        "file_risk": lambda: service.file_risk(data.get("filename"), data.get("mime"), data.get("hash"), data.get("size", 0)),
        "content_create": lambda: service.content_create(data.get("kind", "post"), data.get("title"), data.get("body"), "master_web", **(data.get("options") or {})),
        "content_schedule": lambda: service.content_schedule(data.get("content_id"), data.get("targets") or [], data.get("execute_at"), data.get("recurrence"), data.get("expires_at")),
        "editorial": lambda: service.editorial_decision(data.get("content_id"), "master_web", data.get("decision"), data.get("comment", "")),
        "library": lambda: service.library_save(data.get("title"), data.get("body"), data.get("tags")),
        "render": lambda: service.render_template(data.get("template"), data.get("variables") or {}),
        "translation": lambda: service.translation_job(data.get("content_id"), data.get("languages") or []),
        "keyword": lambda: service.keyword_rule(data.get("group_id"), data.get("keyword"), data.get("response"), data.get("conditions")),
        "form": lambda: service.form_save(data.get("title"), data.get("fields") or [], data.get("destination")),
        "webhook": lambda: service.webhook_save(data.get("group_id"), data.get("url"), data.get("events") or [], data.get("secret")),
        "webhook_enqueue": lambda: service.webhook_enqueue(data.get("event"), data.get("group_id"), data.get("payload") or {}),
        "webhook_result": lambda: service.webhook_result(data.get("job_id"), data.get("success", False), data.get("error", "")),
        "ai_source": lambda: service.ai_source(data.get("group_id"), data.get("title"), data.get("content"), data.get("approved", True)),
        "ai_summary": lambda: service.ai_summary(data.get("group_id"), data.get("messages") or [], data.get("period", "daily"), data.get("topic")),
        "unanswered": lambda: service.unanswered_questions(data.get("messages") or [], data.get("response_window", 10)),
        "topics": lambda: service.classify_topics(data.get("messages") or []),
        "explain": lambda: service.moderation_explanation(data.get("decision"), data.get("evidence") or [], data.get("policy")),
        "model_eval": lambda: service.model_evaluation(data.get("model"), data.get("correct", 0), data.get("total", 0), data.get("latency_ms", 0), data.get("cost", 0)),
        "ab": lambda: service.ab_assignment(data.get("experiment"), data.get("user_id"), data.get("variants") or ["A", "B"]),
        "memory": lambda: service.memory_export(data.get("group_id")),
        "tone": lambda: service.tone_signal(data.get("group_id"), data.get("messages") or []),
        "draft_rules": lambda: service.draft_rules(data.get("community_type"), data.get("priorities") or []),
        "analytics": lambda: service.analytics(data.get("memberships") or [], data.get("messages") or [], data.get("campaigns")),
        "health": lambda: service.health_score(data.get("metrics") or {}),
        "anomaly": lambda: service.anomaly(data.get("metric"), data.get("current", 0), data.get("history") or []),
        "goal": lambda: service.goal(data.get("group_id"), data.get("metric"), data.get("target"), data.get("month")),
        "bi": lambda: service.bi_export(data.get("dataset") or []),
        "report_schedule": lambda: service.report_schedule(data.get("group_id"), data.get("channel"), data.get("frequency"), data.get("recipients") or []),
        "benchmark": lambda: service.anonymous_benchmark(data.get("group_ids") or [], data.get("metric_rows") or {}),
        "module": lambda: service.module_register(data.get("name"), data.get("version"), data.get("permissions") or [], data.get("checksum"), data.get("verified", False)),
        "api_token": lambda: service.api_token(data.get("name"), data.get("scopes") or [], data.get("expires_at")),
        "rotate_token": lambda: service.rotate_token(data.get("token_id")),
        "sandbox": lambda: service.sandbox(data.get("bot_id"), data.get("enabled", True)),
        "quota": lambda: service.quota(data.get("bot_id"), data.get("method"), data.get("used", 0), data.get("limit", 1), data.get("reset_at")),
        "sign_config": lambda: service.signed_config(data.get("payload")),
        "verify_config": lambda: service.verify_config(data.get("bundle") or {}),
        "incident": lambda: service.incident_link(data.get("provider"), data.get("external_id"), data.get("group_id"), data.get("title")),
        "calendar_link": lambda: service.calendar_link(data.get("provider"), data.get("calendar_id"), data.get("group_id"), data.get("sync_token")),
        "sdk": service.sdk_manifest,
        "deployment": lambda: service.deployment(data.get("version"), data.get("instances") or [], data.get("batch_size", 1)),
        "health_result": lambda: service.health_result(data.get("deployment_id"), data.get("instance"), data.get("healthy", False)),
        "backup_policy": lambda: service.backup_policy(data.get("retention_days", 30), data.get("encrypted", True), data.get("modules")),
        "restore_plan": lambda: service.restore_plan(data.get("backup_id"), data.get("groups"), data.get("modules")),
        "dependency": lambda: service.dependency_status(data.get("name"), data.get("status"), data.get("latency_ms"), data.get("detail", "")),
        "resource_alerts": lambda: service.resource_alerts(data.get("metrics") or {}, data.get("thresholds")),
        "degraded": lambda: service.degraded_mode(data.get("dependencies") or {}),
        "diagnose": lambda: service.diagnose(data.get("metrics") or {}, data.get("errors") or []),
        "group_errors": lambda: service.group_errors(data.get("errors") or []),
        "maintenance": lambda: service.maintenance_window(data.get("starts_at"), data.get("ends_at"), data.get("modules") or [], data.get("message", "")),
    }
    if action not in handlers:
        return jsonify({"ok": False, "error": "acción inválida"}), 400
    try:
        result = handlers[action]()
        return jsonify({"ok": result is not None, "result": result}), 200 if result is not None else 404
    except (TypeError, ValueError, KeyError) as error:
        return jsonify({"ok": False, "error": str(error)}), 400
