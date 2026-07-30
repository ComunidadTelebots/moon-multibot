import unittest

from tools.validate_compose_policy import validate


def proxy_service(secret, port, **extra):
    return {
        "image": "telegrammessenger/proxy@sha256:" + "a" * 64,
        "environment": {"SECRET": secret},
        "ports": [{"published": port, "target": 443}],
        **extra,
    }


class ComposeUpdatePolicyTests(unittest.TestCase):
    def valid_proxies(self):
        return {
            "services": {
                f"mtproxy-{index}": proxy_service(str(index) * 32, 8442 + index)
                for index in range(1, 4)
            }
        }

    def test_accepts_exactly_three_isolated_proxies(self):
        validate(self.valid_proxies(), "proxies")

    def test_rejects_duplicate_secrets_or_ports(self):
        document = self.valid_proxies()
        document["services"]["mtproxy-2"]["environment"]["SECRET"] = "1" * 32
        with self.assertRaisesRegex(ValueError, "secrets"):
            validate(document, "proxies")
        document = self.valid_proxies()
        document["services"]["mtproxy-2"]["ports"][0]["published"] = 8443
        with self.assertRaisesRegex(ValueError, "puertos"):
            validate(document, "proxies")

    def test_rejects_extra_proxy_and_privileged_scopes(self):
        document = self.valid_proxies()
        document["services"]["mtproxy-4"] = proxy_service("4" * 32, 8446)
        with self.assertRaisesRegex(ValueError, "exactamente"):
            validate(document, "proxies")
        document = self.valid_proxies()
        document["services"]["mtproxy-1"]["privileged"] = True
        with self.assertRaisesRegex(ValueError, "privileged"):
            validate(document, "proxies")

    def test_rejects_docker_socket_and_host_network(self):
        document = self.valid_proxies()
        document["services"]["mtproxy-1"]["volumes"] = [
            {"source": "/var/run/docker.sock", "target": "/var/run/docker.sock"}
        ]
        with self.assertRaisesRegex(ValueError, "montaje sensible"):
            validate(document, "proxies")
        document = self.valid_proxies()
        document["services"]["mtproxy-1"]["network_mode"] = "host"
        with self.assertRaisesRegex(ValueError, "host network"):
            validate(document, "proxies")

    def test_rejects_mutable_proxy_image_tags(self):
        document = self.valid_proxies()
        document["services"]["mtproxy-1"]["image"] = "telegrammessenger/proxy:latest"
        with self.assertRaisesRegex(ValueError, "digest"):
            validate(document, "proxies")

    def test_rejects_multiple_secrets_ports_build_and_mount_descendants(self):
        document = self.valid_proxies()
        document["services"]["mtproxy-1"]["environment"]["FAKE_SECRET"] = "f" * 32
        with self.assertRaisesRegex(ValueError, "exactamente un secret"):
            validate(document, "proxies")
        document = self.valid_proxies()
        document["services"]["mtproxy-1"]["ports"].append({"published": 9443, "target": 443})
        with self.assertRaisesRegex(ValueError, "exactamente un puerto"):
            validate(document, "proxies")
        document = self.valid_proxies()
        document["services"]["mtproxy-1"]["build"] = {"context": "."}
        with self.assertRaisesRegex(ValueError, "build local"):
            validate(document, "proxies")
        document = self.valid_proxies()
        document["services"]["mtproxy-1"]["volumes"] = [{"source": "/etc/passwd", "target": "/tmp/passwd"}]
        with self.assertRaisesRegex(ValueError, "montaje sensible"):
            validate(document, "proxies")


if __name__ == "__main__":
    unittest.main()
