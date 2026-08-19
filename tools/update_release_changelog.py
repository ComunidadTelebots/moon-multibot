"""Regenera el inventario exacto de funciones incorporadas por versión."""

from importlib import import_module
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


START = "<!-- GENERATED_RELEASE_FEATURES_START -->"
END = "<!-- GENERATED_RELEASE_FEATURES_END -->"
RELEASES = {
    "v18.22.0": (
        "webapp_content_security_ai_operations_manifest",
        "webapp_ai_accounts_creator_operations_manifest",
        "resource_grouped_routing_cache_rotation_manifest",
        "webapp_creator_news_proxy_operations_manifest",
        "resource_rotation_archive_restore_observability_quality_manifest",
    ),
    "v18.23.0": (
        "webapp_proxy_dashboard_analytics_operations_manifest",
        "webapp_analytics_privacy_seo_operations_manifest",
    ),
    "v18.23.1": (
        "webapp_seo_community_support_operations_manifest",
        "resource_quality_sandbox_governance_impact_manifest",
        "webapp_support_subscription_moderation_operations_manifest",
    ),
    "v18.23.3": (
        "resource_energy_abuse_migration_federation_manifest",
        "webapp_moderation_security_ai_operations_manifest",
    ),
    "v18.23.4": (
        "resource_federation_continuity_assistance_manifest",
        "webapp_ai_group_channel_operations_manifest",
    ),
    "v18.23.5": (
        "webapp_channel_user_automation_operations_manifest",
    ),
    "v18.23.7": (
        "webapp_automation_media_bot_operations_manifest",
    ),
}


def entries(module_name):
    module = import_module(module_name)
    return getattr(module, "FEATURES", None) or getattr(module, "MANIFEST", ())


def render():
    lines = [START, "## Inventario exacto por versión", ""]
    for version, modules in RELEASES.items():
        rows = [item for module in modules for item in entries(module)]
        lines.extend((f"### {version} — {len(rows)} funciones incorporadas", ""))
        for item in rows:
            lines.append(
                f"- `{item['id']}` · `{item['api']}` — {item.get('title') or item.get('capability')}"
            )
        lines.append("")
    lines.append(END)
    return "\n".join(lines)


def main():
    path = ROOT / "CHANGELOG.md"
    content = path.read_text(encoding="utf-8-sig")
    generated = render()
    if START in content and END in content:
        prefix, rest = content.split(START, 1)
        _, suffix = rest.split(END, 1)
        content = prefix + generated + suffix
    else:
        first_break = content.find("\n")
        content = content[: first_break + 1] + "\n" + generated + "\n" + content[first_break + 1 :]
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
