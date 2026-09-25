"""Retire the legacy CPU-only autoscaler until token ownership is coordinated.

Starting replicas from identical bot configuration can duplicate Telegram
receivers. This compatibility entrypoint intentionally performs no Docker calls.
"""


def main():
    print("Legacy release autoscaler quarantined: use explicit worker assignments; automatic recreation disabled.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
