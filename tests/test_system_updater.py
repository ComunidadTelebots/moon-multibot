from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SystemUpdaterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.updater = (ROOT / "update-system.sh").read_text(encoding="utf-8")
        cls.start = (ROOT / "start.sh").read_text(encoding="utf-8-sig")

    def test_existing_env_files_are_applied_without_sourcing_or_copying(self):
        self.assertIn('--env-file "$MOONBOT_ENV_FILE"', self.updater)
        self.assertIn('--env-file "$MTPROTO_ENV_FILE"', self.updater)
        self.assertNotIn("source $", self.updater)
        self.assertNotIn("cp .env", self.updater)
        self.assertNotIn("cat $MOONBOT_ENV_FILE", self.updater)

    def test_updates_exactly_three_proxies_and_excludes_ollama(self):
        for service in ("mtproxy-1", "mtproxy-2", "mtproxy-3"):
            self.assertIn(service, self.updater)
        self.assertIn('build moonbot', self.updater)
        self.assertNotIn('up -d moon_ollama', self.updater)

    def test_git_update_is_fast_forward_and_dirty_tree_fails_closed(self):
        self.assertIn("status --porcelain --untracked-files=normal", self.updater)
        self.assertNotIn("pull --ff-only", self.updater)
        self.assertIn('merge --ff-only "$fetched_sha"', self.updater)
        self.assertIn("rev-parse --verify FETCH_HEAD", self.updater)
        self.assertIn("merge-base --is-ancestor", self.updater)
        self.assertIn("ComunidadTelebots", self.updater)
        self.assertIn('branch" = "$expected_branch', self.updater)
        self.assertIn("preflight_moonbot; preflight_proxies;", self.updater)

    def test_env_symlinks_and_unexpected_proxy_instances_are_rejected(self):
        self.assertIn('[ ! -L "$env_file" ]', self.updater)
        self.assertIn("grep -Ev '^mtproxy-[123]$'", self.updater)
        self.assertIn('permisos 600 o 640', self.updater)
        self.assertIn("validate_compose_policy.py", self.updater)

    def test_normal_startup_never_pulls_code(self):
        self.assertNotIn("git pull origin master", self.start)

    def test_health_waits_and_flock_is_required(self):
        self.assertIn("require_command flock", self.updater)
        self.assertIn('while [ "$health" = "starting" ]', self.updater)

    def test_component_updates_prepare_automatic_container_rollback(self):
        self.assertIn("prepare_component_rollback", self.updater)
        self.assertIn("rollback_active_component", self.updater)
        self.assertIn("trap on_error ERR", self.updater)
        self.assertIn("image_id", self.updater)
        self.assertNotIn("down -v", self.updater)

    def test_start_delegates_update_before_setup_and_runtime(self):
        dispatch = self.start.index('"system-update"')
        migration = self.start.index("# Ejecutar migración automática antes de arrancar")
        self.assertLess(dispatch, migration)
        self.assertIn('update-system.sh', self.start)


if __name__ == "__main__":
    unittest.main()
