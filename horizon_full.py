"""Unified executable catalog for the 100 Horizonte 202 capabilities."""

from horizon_completion import FEATURES, HorizonCompletion
from roadmap_engine import RoadmapEngine


CORE_FEATURES = {
    "conversation_escalation": ("Radar de conversaciones que están escalando", "moderation"),
    "mediator": ("Modo mediador con turnos de palabra", "moderation"),
    "coordinated_brigade": ("Detección de brigadas externas coordinadas", "moderation"),
    "domain_quarantine": ("Cuarentena de enlaces recién registrados", "moderation"),
    "reputation_passport": ("Pasaporte de reputación consentido", "moderation"),
    "peer_review": ("Revisión por pares para sanciones dudosas", "moderation"),
    "rule_impact": ("Simulador de impacto antes de cambiar una regla", "moderation"),
    "voice_clone_risk": ("Detector de estafas por clonación de voz", "moderation"),
    "incident_timeline": ("Mapa temporal de incidentes por tema", "moderation"),
    "evidence_chain": ("Cadena de custodia firmada para evidencias", "moderation"),
    "assembly": ("Asambleas con propuestas y enmiendas", "community"),
    "participatory_budget": ("Presupuesto comunitario con votos ponderados", "community"),
    "interest_circle": ("Círculos temporales por intereses", "community"),
    "time_bank": ("Banco de tiempo entre miembros", "community"),
    "welcome_round": ("Rondas automáticas de bienvenida humana", "community"),
    "collaborative_mission": ("Misiones colaborativas entre varios grupos", "community"),
    "invisible_contributions": ("Reconocimiento de contribuciones invisibles", "community"),
    "social_health": ("Panel de salud social agregado", "community"),
    "admin_relay": ("Sistema de relevos para administradores", "community"),
    "annual_memory": ("Memoria anual generada por la comunidad", "community"),
    "editorial_series": ("Editor de series editoriales conectadas", "content"),
    "content_reuse": ("Reutilización inteligente de contenido antiguo", "content"),
    "silence_calendar": ("Calendario de silencios", "content"),
    "headline_comparison": ("Comparador de titulares", "content"),
    "public_announcement": ("Versionado público de comunicados", "content"),
}


class FullHorizonSuite:
    def __init__(self, db):
        self.db = db
        self.roadmap = RoadmapEngine(db)
        self.completion = HorizonCompletion(db)

    def catalog(self):
        core = [{"slug": slug, "title": title, "category": category, "engine": "roadmap"}
                for slug, (title, category) in CORE_FEATURES.items()]
        completion = [{**row, "engine": "completion"} for row in self.completion.catalog()]
        return core + completion

    def audit(self):
        return (self.completion._list("HORIZON_COMPLETION_AUDIT") +
                self.completion._list("ROADMAP_AUDIT"))[-250:]

    def execute(self, slug, data=None):
        data = data if isinstance(data, dict) else {}
        if slug in FEATURES:
            return self.completion.execute(slug, data)
        handlers = {
            "conversation_escalation": lambda: self.roadmap.conversation_escalation(data.get("group_id"), data.get("samples") or [], data.get("window_seconds", 300)),
            "mediator": lambda: self.roadmap.mediator_session(data.get("group_id"), data.get("operation"), data.get("user_id"), data.get("statement")),
            "coordinated_brigade": lambda: self.roadmap.coordinated_brigade(data.get("events") or [], data.get("minimum_groups", 2), data.get("minimum_users", 3)),
            "domain_quarantine": lambda: self.roadmap.domain_quarantine(data.get("url"), data.get("domain_age_days"), data.get("trusted_domains") or [], data.get("minimum_age_days", 30)),
            "reputation_passport": lambda: self.roadmap.reputation_passport(data.get("user_id"), data.get("metrics") or {}, data.get("consent", False)),
            "peer_review": lambda: self.roadmap.peer_review(data.get("operation"), data.get("case_id"), data.get("reviewer_id"), data.get("verdict"), data.get("payload"), data.get("quorum", 3)),
            "rule_impact": lambda: self.roadmap.rule_impact_simulation(data.get("group_id"), data.get("rule") or {}, data.get("samples") or []),
            "voice_clone_risk": lambda: self.roadmap.voice_clone_risk(data.get("features") or {}),
            "incident_timeline": lambda: self.roadmap.incident_timeline(data.get("group_id"), data.get("operation", "list"), data.get("event")),
            "evidence_chain": lambda: self.roadmap.evidence_chain(data.get("case_id"), data.get("operation", "append"), data.get("evidence")),
            "assembly": lambda: self.roadmap.assembly(data.get("group_id"), data.get("operation"), data.get("assembly_id"), data.get("actor_id"), data),
            "participatory_budget": lambda: self.roadmap.participatory_budget(data.get("group_id"), data.get("operation"), data.get("budget_id"), data.get("user_id"), data),
            "interest_circle": lambda: self.roadmap.interest_circle(data.get("group_id"), data.get("operation"), data.get("circle_id"), data.get("user_id"), data),
            "time_bank": lambda: self.roadmap.time_bank(data.get("group_id"), data.get("operation"), data.get("user_id"), data.get("target_id"), data.get("hours", 0), data.get("note", "")),
            "welcome_round": lambda: self.roadmap.welcome_round(data.get("group_id"), data.get("member_id"), data.get("hosts") or [], data.get("capacity", 3)),
            "collaborative_mission": lambda: self.roadmap.collaborative_mission(data.get("operation", "create"), data.get("group_ids"), data.get("mission_id"), data.get("user_id"), data.get("title", ""), data.get("target", 1), data.get("progress", 0)),
            "invisible_contributions": lambda: self.roadmap.invisible_contributions(data.get("group_id"), data.get("events") or []),
            "social_health": lambda: self.roadmap.social_health(data.get("group_id"), data.get("metrics") or {}),
            "admin_relay": lambda: self.roadmap.admin_relay(data.get("group_id"), data.get("operation", "create"), data.get("outgoing_id"), data.get("incoming_id"), data.get("starts_at"), data.get("ends_at"), data.get("relay_id")),
            "annual_memory": lambda: self.roadmap.annual_memory(data.get("group_id"), data.get("year"), data.get("highlights"), data.get("metrics"), data.get("contributors")),
            "editorial_series": lambda: self.roadmap.editorial_series(data.get("operation", "create"), data.get("series_id"), data.get("title", ""), data.get("description", ""), data.get("content_id"), data.get("position")),
            "content_reuse": lambda: self.roadmap.content_reuse_candidates(data.get("items") or [], data.get("minimum_age_days", 30), data.get("limit", 20)),
            "silence_calendar": lambda: self.roadmap.silence_calendar(data.get("group_id"), data.get("operation", "check"), data.get("starts_at"), data.get("ends_at"), data.get("reason", ""), data.get("window_id"), data.get("check_at")),
            "headline_comparison": lambda: self.roadmap.compare_headlines(data.get("headlines") or []),
            "public_announcement": lambda: self.roadmap.public_announcement_version(data.get("operation", "publish"), data.get("announcement_id"), data.get("title", ""), data.get("body", ""), data.get("correction_note", ""), data.get("actor_id")),
        }
        if slug not in handlers:
            raise ValueError("función Horizonte 202 desconocida")
        return handlers[slug]()
