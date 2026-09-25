# Release startup protection

Release images must contain start.sh, moon_multibot.py and core/config.py.
Never bind an empty checkout over /app: it hides the image contents. Mount only
isolated data/downloads directories for each release. Do not share bot ownership
with a running receiver.

Mount tools/release_startup.py read-only at /opt/moon/release_startup.py and use
`command: [python, /opt/moon/release_startup.py]`. Set `AUTO_DOCKER_UPDATE=false`,
`restart: "on-failure:5"`, and `profiles: [release-manual]`. Leave
`MOON_RELEASE_ENABLED=false` until isolated credentials, plugin compatibility,
health and exclusive bot assignment have been verified. Explicit service startup
bypasses Compose profiles, so the entrypoint also enforces quarantine.

Validate the Compose configuration and image files without network/credentials
before starting a release. Keep the previous immutable image and configuration
for rollback. Never promote a release solely because the process starts.

The legacy CPU-only autoscaler must remain stopped with restart policy `no`.
Its replacement entrypoint tools/release_autoscaler_guard.py exits without Docker
calls even if an operator starts the old container. Re-enable automated scaling
only through a controller that coordinates exclusive token ownership and queues.

These guards intentionally do not implement distributed jobs, routing, automatic
rollback or UI alerts. Existing worker health/restart telemetry remains available.
